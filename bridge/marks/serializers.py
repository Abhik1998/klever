import re
import json

from django.utils.translation import ugettext_lazy as _

from rest_framework import fields, serializers, exceptions
from rest_framework.serializers import PrimaryKeyRelatedField

from bridge.vars import MPTT_FIELDS
from bridge.utils import logger

from reports.models import ReportSafe, ReportUnsafe, ReportUnknown
from marks.models import (
    MAX_TAG_LEN, SafeTag, UnsafeTag,
    MarkSafe, MarkSafeHistory, MarkSafeAttr, MarkSafeTag,
    MarkUnsafe, MarkUnsafeHistory, MarkUnsafeAttr, MarkUnsafeTag, ConvertedTrace,
    MarkUnknown, MarkUnknownHistory, MarkUnknownAttr, SafeTagAccess, UnsafeTagAccess
)
from marks.UnsafeUtils import save_converted_trace, CONVERT_FUNCTIONS, COMPARE_FUNCTIONS


def create_mark_version(mark, cache=True, **kwargs):
    """
    Creates mark version (MarkSafeHistory, MarkUnsafeHistory, MarkUnknownHistory) without any checks.
    :param mark: MarkSafe, MarkUnsafe, MarkUnknown instance
    :param cache: is caching needed?
    :param kwargs: mark version fields
    :return:
    """
    kwargs.setdefault('version', mark.version)
    kwargs.setdefault('author', mark.author)

    kwargs.pop('autoconfirm', False)
    attrs = kwargs.pop('attrs')
    tags = kwargs.pop('tags', [])

    mark_version = None

    if isinstance(mark, MarkSafe):
        mark_version = MarkSafeHistory.objects.create(mark=mark, **kwargs)
        MarkSafeTag.objects.bulk_create(list(MarkSafeTag(tag_id=t, mark_version=mark_version) for t in tags))
        MarkSafeAttr.objects.bulk_create(list(MarkSafeAttr(mark_version=mark_version, **attr) for attr in attrs))

        if cache:
            mark.cache_tags = list(SafeTag.objects.filter(id__in=tags).order_by('name').values_list('name', flat=True))
            mark.cache_attrs = dict((attr['name'], attr['value']) for attr in attrs if attr['is_compare'])
            mark.save()
    elif isinstance(mark, MarkUnsafe):
        mark_version = MarkUnsafeHistory.objects.create(mark=mark, **kwargs)
        MarkUnsafeTag.objects.bulk_create(list(MarkUnsafeTag(tag_id=t, mark_version=mark_version) for t in tags))
        MarkUnsafeAttr.objects.bulk_create(list(MarkUnsafeAttr(mark_version=mark_version, **attr) for attr in attrs))

        if cache:
            mark.error_trace = mark_version.error_trace
            mark.cache_tags = list(UnsafeTag.objects.filter(id__in=tags).order_by('name')
                                   .values_list('name', flat=True))
            mark.cache_attrs = dict((attr['name'], attr['value']) for attr in attrs if attr['is_compare'])
            mark.save()
    elif isinstance(mark, MarkUnknown):
        mark_version = MarkUnknownHistory.objects.create(mark=mark, **kwargs)
        MarkUnknownAttr.objects.bulk_create(list(MarkUnknownAttr(mark_version=mark_version, **attr) for attr in attrs))

        if cache:
            mark.cache_attrs = dict((attr['name'], attr['value']) for attr in attrs if attr['is_compare'])
            mark.save()
    return mark_version


class SafeTagSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, SafeTag):
            if data['parent'] is None:
                data['parent'] = 0

            unavailable = set(instance.get_descendants(include_self=True).values_list('id', flat=True))
            data['parents'] = [{'id': 0, 'name': str(_('Root'))}]
            for t in SafeTag.objects.order_by('name'):
                if t.id not in unavailable:
                    data['parents'].append({'id': t.id, 'name': t.name})
        return data

    class Meta:
        model = SafeTag
        exclude = MPTT_FIELDS


class UnsafeTagSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, UnsafeTag):
            if data['parent'] is None:
                data['parent'] = 0

            unavailable = set(instance.get_descendants(include_self=True).values_list('id', flat=True))
            data['parents'] = [{'id': 0, 'name': str(_('Root'))}]
            for t in UnsafeTag.objects.order_by('name'):
                if t.id not in unavailable:
                    data['parents'].append({'id': t.id, 'name': t.name})
        return data

    class Meta:
        model = UnsafeTag
        exclude = MPTT_FIELDS


class WithTagsMixin:
    def get_tags_ids(self, tags, tags_qs):
        if not hasattr(self, 'Meta'):
            raise RuntimeError('Incorrect mixin usage')

        if not tags:
            # Empty list
            return tags

        context = getattr(self, 'context')
        if 'tags_tree' in context:
            tags_tree = context['tags_tree']
        else:
            tags_tree = dict((t.id, t.parent_id) for t in tags_qs)
        if 'tags_names' in context:
            tags_names = context['tags_names']
        else:
            tags_names = dict((t.name, t.id) for t in tags_qs)

        # Collect tags with all ascendants
        mark_tags = set()
        for t_name in tags:
            if t_name not in tags_names:
                raise exceptions.ValidationError(_('One of tags was not found'))
            parent = tags_names[t_name]
            while parent:
                if parent in mark_tags:
                    break
                mark_tags.add(parent)
                parent = tags_tree[parent]
        return list(mark_tags)


class SafeMarkAttrSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkSafeAttr
        exclude = ('mark_version',)


class UnsafeMarkAttrSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkUnsafeAttr
        exclude = ('mark_version',)


class UnknownMarkAttrSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkUnknownAttr
        exclude = ('mark_version',)


class SafeMarkVersionSerializer(WithTagsMixin, serializers.ModelSerializer):
    tags = fields.ListField(child=fields.CharField(max_length=MAX_TAG_LEN), allow_empty=True)
    autoconfirm = fields.BooleanField(default=False)
    attrs = fields.ListField(child=SafeMarkAttrSerializer(), allow_empty=True)

    def validate_tags(self, tags):
        return self.get_tags_ids(tags, SafeTag.objects.all())

    def get_value(self, dictionary):
        return dictionary

    def create(self, validated_data):
        if 'mark' not in validated_data:
            raise exceptions.ValidationError(detail={'mark': 'Required'})
        return create_mark_version(validated_data.pop('mark'), **validated_data)

    def update(self, instance, validated_data):
        raise RuntimeError('Update of mark version object is not allowed')

    class Meta:
        model = MarkSafeHistory
        fields = ('status', 'change_date', 'comment', 'description', 'verdict', 'tags', 'autoconfirm', 'attrs')


class SafeMarkSerializer(serializers.ModelSerializer):
    mark_version = SafeMarkVersionSerializer(write_only=True)

    def create(self, validated_data):
        # Save kwargs:
        # identifier - preset and upload
        # job - GUI creation
        # format - upload
        # version - upload
        # author - upload (null for preset)

        version_data = validated_data.pop('mark_version')

        if validated_data.get('job'):
            validated_data['format'] = validated_data['job'].format

        # Get user from context (on GUI creation)
        if 'request' in self.context:
            validated_data['author'] = self.context['request'].user

        instance = super().create(validated_data)
        create_mark_version(instance, **version_data)
        return instance

    def update(self, instance, validated_data):
        assert isinstance(instance, MarkSafe)
        version_data = validated_data.pop('mark_version')
        validated_data['version'] = instance.version + 1

        instance = super().update(instance, validated_data)
        create_mark_version(instance, **version_data)
        return instance

    def to_representation(self, instance):
        value = super().to_representation(instance)
        if isinstance(instance, MarkSafe):
            last_version = MarkSafeHistory.objects.get(mark=instance, version=instance.version)
            value['mark_version'] = SafeMarkVersionSerializer(instance=last_version).data
        return value

    class Meta:
        model = MarkSafe
        fields = ('is_modifiable', 'verdict', 'mark_version')


class UnsafeMarkVersionSerializer(WithTagsMixin, serializers.ModelSerializer):
    autoconfirm = fields.BooleanField(default=False)
    attrs = fields.ListField(child=UnsafeMarkAttrSerializer(), allow_empty=True)
    error_trace = fields.CharField(write_only=True, required=False)

    def validate_tags(self, tags):
        return self.get_tags_ids(tags, UnsafeTag.objects.all())

    def __validate_error_trace(self, err_trace_str, compare_func):
        try:
            convert_func = COMPARE_FUNCTIONS[compare_func]['convert']
            assert convert_func in CONVERT_FUNCTIONS
            forests = json.loads(err_trace_str)
            # TODO: is it enough? Or we need deeper check of forests format?
            assert isinstance(forests, list)
            return save_converted_trace(forests, convert_func)
        except Exception as e:
            logger.exception(e)
            raise exceptions.ValidationError(detail={'error_trace': _('Wrong error trace json provided')})

    def validate(self, attrs):
        res = super().validate(attrs)
        if 'error_trace' in res:
            res['error_trace'] = self.__validate_error_trace(res.pop('error_trace'), res['function'])
        return res

    def get_value(self, dictionary):
        return dictionary

    def create(self, validated_data):
        if 'mark' not in validated_data:
            raise exceptions.ValidationError(detail={'mark': 'Required'})
        if 'error_trace' not in validated_data:
            raise exceptions.ValidationError(detail={'error_trace': 'Required'})
        return create_mark_version(validated_data.pop('mark'), **validated_data)

    def update(self, instance, validated_data):
        raise RuntimeError('Update of mark version object is not allowed')

    def to_representation(self, instance):
        res = super().to_representation(instance)
        if isinstance(instance, MarkUnsafeHistory):
            conv = ConvertedTrace.objects.get(id=instance.error_trace_id)
            with conv.file.file as fp:
                res['error_trace'] = fp.read().decode('utf-8')
        return res

    class Meta:
        model = MarkUnsafeHistory
        fields = (
            'status', 'change_date', 'comment', 'description', 'verdict', 'tags', 'autoconfirm', 'attrs',
            'function', 'error_trace'
        )


class UnsafeMarkSerializer(serializers.ModelSerializer):
    mark_version = UnsafeMarkVersionSerializer(write_only=True)

    def create(self, validated_data):
        # Save kwargs:
        # identifier - preset and upload
        # job - GUI creation
        # format - upload
        # version - upload
        # author - upload (null for preset)
        # error_trace - always (ConvertedTrace instance)

        version_data = validated_data.pop('mark_version')

        if 'error_trace' in validated_data:
            # ConvertedTrace instance from save kwargs
            version_data['error_trace'] = validated_data['error_trace']
        elif 'error_trace' in version_data:
            # ConvertedTrace object from version serializer, used in population and upload
            validated_data['error_trace'] = version_data['error_trace']
        else:
            raise exceptions.ValidationError(detail={'error_trace': 'Required'})

        if validated_data.get('job'):
            validated_data['format'] = validated_data['job'].format

        # Get user from context (on GUI creation)
        if 'request' in self.context:
            validated_data['author'] = self.context['request'].user

        instance = super().create(validated_data)
        create_mark_version(instance, **version_data)
        return instance

    def update(self, instance, validated_data):
        assert isinstance(instance, MarkUnsafe)
        version_data = validated_data.pop('mark_version')
        validated_data['version'] = instance.version + 1

        instance = super().update(instance, validated_data)
        create_mark_version(instance, **version_data)
        return instance

    def to_representation(self, instance):
        value = super().to_representation(instance)
        if isinstance(instance, MarkUnsafe):
            last_version = MarkUnsafeHistory.objects.get(mark=instance, version=instance.version)
            value['mark_version'] = UnsafeMarkVersionSerializer(instance=last_version).data
        return value

    class Meta:
        model = MarkUnsafe
        fields = ('is_modifiable', 'verdict', 'mark_version', 'function')


class UnknownMarkVersionSerializer(serializers.ModelSerializer):
    autoconfirm = fields.BooleanField(default=False)
    attrs = fields.ListField(child=UnsafeMarkAttrSerializer(), allow_empty=True)

    def validate(self, attrs):
        res = super().validate(attrs)
        if res.get('is_regexp'):
            try:
                re.search(res['function'], '')
            except Exception as e:
                logger.exception(e)
                raise exceptions.ValidationError(detail={
                    'function': _("The pattern is wrong, please refer to documentation on the standard "
                                  "Python library for processing reqular expressions")
                })
        return res

    def get_value(self, dictionary):
        return dictionary

    def create(self, validated_data):
        if 'mark' not in validated_data:
            raise exceptions.ValidationError(detail={'mark': 'Required'})
        return create_mark_version(validated_data.pop('mark'), **validated_data)

    def update(self, instance, validated_data):
        raise RuntimeError('Update of mark version object is not allowed')

    class Meta:
        model = MarkUnknownHistory
        fields = (
            'status', 'change_date', 'comment', 'description', 'autoconfirm', 'attrs',
            'function', 'is_regexp', 'problem_pattern', 'link'
        )


class UnknownMarkSerializer(serializers.ModelSerializer):
    mark_version = UnknownMarkVersionSerializer(write_only=True)

    def create(self, validated_data):
        # Save kwargs:
        # identifier - preset and upload
        # job - GUI creation
        # format - upload
        # version - upload
        # author - upload (null for preset)

        version_data = validated_data.pop('mark_version')

        if validated_data.get('job'):
            validated_data['format'] = validated_data['job'].format

        # Get user from context (on GUI creation)
        if 'request' in self.context:
            validated_data['author'] = self.context['request'].user

        instance = super().create(validated_data)
        create_mark_version(instance, **version_data)
        return instance

    def update(self, instance, validated_data):
        assert isinstance(instance, MarkUnsafe)
        version_data = validated_data.pop('mark_version')
        validated_data['version'] = instance.version + 1

        instance = super().update(instance, validated_data)
        create_mark_version(instance, **version_data)
        return instance

    def to_representation(self, instance):
        value = super().to_representation(instance)
        if isinstance(instance, MarkUnknown):
            last_version = MarkUnknownHistory.objects.get(mark=instance, version=instance.version)
            value['mark_version'] = UnknownMarkVersionSerializer(instance=last_version).data
        return value

    class Meta:
        model = MarkUnknown
        fields = ('is_modifiable', 'mark_version', 'function', 'is_regexp', 'problem_pattern', 'link')


class SMVlistSerializerRO(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, instance):
        if instance.mark.version == instance.version:
            return _("Current version")
        title = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S").to_representation(instance.change_date)
        if instance.author:
            title += ' ({0})'.format(instance.author.get_full_name())
        if instance.comment:
            title += ': {0}'.format(instance.comment)
        return title

    class Meta:
        model = MarkSafeHistory
        fields = ('version', 'title')


class SMSerializerRO(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    def get_author(self, instance):
        if not instance.author:
            return None

    class Meta:
        model = MarkSafe
        fields = ('version', 'title')


def test_safe_mark():
    with open('marks/presets/safes/a154f9cc-927d-4e8b-b095-3ee7391db667.json', mode='r') as fp:
        data = json.load(fp)
    s = SafeMarkSerializer(data=data)
    s.is_valid(raise_exception=True)
    return s

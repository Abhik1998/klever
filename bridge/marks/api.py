import json

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from rest_framework import status, exceptions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.generics import get_object_or_404, RetrieveAPIView, GenericAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bridge.vars import USER_ROLES, ASSOCIATION_TYPE
from bridge.access import ManagerPermission
from tools.profiling import LoggedCallMixin

from users.models import User
from reports.models import ReportSafe, ReportUnsafe, ReportUnknown
from marks.models import (
    MarkSafe, MarkUnsafe, MarkUnknown, SafeTag, UnsafeTag, MarkSafeReport, MarkUnsafeReport, MarkUnknownReport,
    SafeTagAccess, UnsafeTagAccess, SafeAssociationLike, UnsafeAssociationLike, UnknownAssociationLike
)
from marks.utils import MarkAccess
from marks.tags import TagAccess, ChangeTagsAccess, UploadTags
from marks.serializers import (
    SafeMarkSerializer, UnsafeMarkSerializer, UnknownMarkSerializer, SafeTagSerializer, UnsafeTagSerializer
)
from marks.SafeUtils import (
    perform_safe_mark_create, perform_safe_mark_update, remove_safe_marks,
    confirm_safe_mark, unconfirm_safe_mark
)
from marks.UnsafeUtils import (
    perform_unsafe_mark_create, perform_unsafe_mark_update, remove_unsafe_marks,
    confirm_unsafe_mark, unconfirm_unsafe_mark
)
from marks.UnknownUtils import (
    perform_unknown_mark_create, perform_unknown_mark_update, CheckUnknownFunction, remove_unknown_marks,
    confirm_unknown_mark, unconfirm_unknown_mark
)

from caches.utils import UpdateSafeMarksTags, UpdateUnsafeMarksTags


class MarkSafeViewSet(LoggedCallMixin, ModelViewSet):
    parser_classes = (JSONParser, FormParser)
    permission_classes = (IsAuthenticated,)
    queryset = MarkSafe.objects.all()
    serializer_class = SafeMarkSerializer

    def get_unparallel(self, request):
        return [MarkSafe] if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} else []

    def create(self, request, *args, **kwargs):
        report = get_object_or_404(ReportSafe, pk=request.data.get('report_id', 0))
        if not MarkAccess(request.user, report=report).can_create:
            raise exceptions.PermissionDenied(_("You don't have an access to create new marks"))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mark, cache_id = perform_safe_mark_create(self.request.user, report, serializer)
        changes_url = '{}?mark_id={}'.format(reverse('marks:safe-ass-changes', args=[cache_id]), mark.id)
        return Response({'url': changes_url}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Partial update is not allowed
        instance = self.get_object()
        if not MarkAccess(request.user, mark=instance).can_edit:
            raise exceptions.PermissionDenied(_("You don't have an access to edit this mark"))

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        cache_id = perform_safe_mark_update(self.request.user, serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        changes_url = '{}?mark_id={}'.format(reverse('marks:safe-ass-changes', args=[cache_id]), instance.id)
        return Response({'url': changes_url})

    def perform_destroy(self, instance):
        if not MarkAccess(self.request.user, mark=instance).can_delete:
            raise exceptions.PermissionDenied(_("You don't have an access to remove this mark"))
        remove_safe_marks(id=instance.id)


class MarkUnsafeViewSet(LoggedCallMixin, ModelViewSet):
    parser_classes = (JSONParser,)
    permission_classes = (IsAuthenticated,)
    queryset = MarkUnsafe.objects.all()
    serializer_class = UnsafeMarkSerializer

    def get_unparallel(self, request):
        return [MarkUnsafe] if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} else []

    def create(self, request, *args, **kwargs):
        report = get_object_or_404(ReportUnsafe, pk=request.data.get('report_id', 0))
        if not MarkAccess(request.user, report=report).can_create:
            raise exceptions.PermissionDenied(_("You don't have an access to create new marks"))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mark, cache_id = perform_unsafe_mark_create(self.request.user, report, serializer)
        changes_url = '{}?mark_id={}'.format(reverse('marks:unsafe-ass-changes', args=[cache_id]), mark.id)
        return Response({'url': changes_url}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Partial update is not allowed
        instance = self.get_object()
        if not MarkAccess(request.user, mark=instance).can_edit:
            raise exceptions.PermissionDenied(_("You don't have an access to edit this mark"))

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        cache_id = perform_unsafe_mark_update(self.request.user, serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        changes_url = '{}?mark_id={}'.format(reverse('marks:unsafe-ass-changes', args=[cache_id]), instance.id)
        return Response({'url': changes_url})

    def perform_destroy(self, instance):
        if not MarkAccess(self.request.user, mark=instance).can_delete:
            raise exceptions.PermissionDenied(_("You don't have an access to remove this mark"))
        remove_unsafe_marks(id=instance.id)


class MarkUnknownViewSet(LoggedCallMixin, ModelViewSet):
    parser_classes = (JSONParser,)
    permission_classes = (IsAuthenticated,)
    queryset = MarkUnknown.objects.all()
    serializer_class = UnknownMarkSerializer

    def get_unparallel(self, request):
        return [MarkUnknown] if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} else []

    def create(self, request, *args, **kwargs):
        report = get_object_or_404(ReportUnknown, pk=request.data.get('report_id', 0))
        if not MarkAccess(request.user, report=report).can_create:
            raise exceptions.PermissionDenied(_("You don't have an access to create new marks"))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mark, cache_id = perform_unknown_mark_create(self.request.user, report, serializer)
        changes_url = '{}?mark_id={}'.format(reverse('marks:unknown-ass-changes', args=[cache_id]), mark.id)
        return Response({'url': changes_url}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Partial update is not allowed
        instance = self.get_object()
        if not MarkAccess(request.user, mark=instance).can_edit:
            raise exceptions.PermissionDenied(_("You don't have an access to edit this mark"))

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        cache_id = perform_unknown_mark_update(self.request.user, serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        changes_url = '{}?mark_id={}'.format(reverse('marks:unknown-ass-changes', args=[cache_id]), instance.id)
        return Response({'url': changes_url})

    def perform_destroy(self, instance):
        if not MarkAccess(self.request.user, mark=instance).can_delete:
            raise exceptions.PermissionDenied(_("You don't have an access to remove this mark"))
        remove_unknown_marks(id=instance.id)


class SafeTagViewSet(LoggedCallMixin, ModelViewSet):
    parser_classes = (JSONParser,)
    permission_classes = (IsAuthenticated,)
    queryset = SafeTag.objects.all()
    serializer_class = SafeTagSerializer

    def get_unparallel(self, request):
        return [SafeTag] if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} else []

    def perform_create(self, serializer):
        parent = serializer.validated_data.get('parent')
        if not TagAccess(self.request.user, parent).create:
            raise exceptions.PermissionDenied(_("You don't have an access to create this tag"))
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if not TagAccess(self.request.user, serializer.instance).edit:
            raise exceptions.PermissionDenied(_("You don't have an access to edit this tag"))
        serializer.save(author=self.request.user)
        UpdateSafeMarksTags()

    def perform_destroy(self, instance):
        if not TagAccess(self.request.user, instance).delete:
            raise exceptions.PermissionDenied(_("You don't have an access to delete this tag"))
        super().perform_destroy(instance)
        UpdateSafeMarksTags()


class UnsafeTagViewSet(LoggedCallMixin, ModelViewSet):
    parser_classes = (JSONParser,)
    permission_classes = (IsAuthenticated,)
    queryset = UnsafeTag.objects.all()
    serializer_class = UnsafeTagSerializer

    def get_unparallel(self, request):
        return [UnsafeTag] if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} else []

    def perform_create(self, serializer):
        parent = serializer.validated_data.get('parent')
        if not TagAccess(self.request.user, parent).create:
            raise exceptions.PermissionDenied(_("You don't have an access to create this tag"))
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if not TagAccess(self.request.user, serializer.instance).edit:
            raise exceptions.PermissionDenied(_("You don't have an access to edit this tag"))
        serializer.save(author=self.request.user)
        UpdateUnsafeMarksTags()

    def perform_destroy(self, instance):
        if not TagAccess(self.request.user, instance).delete:
            raise exceptions.PermissionDenied(_("You don't have an access to delete this tag"))
        super().perform_destroy(instance)
        UpdateUnsafeMarksTags()


class TagAccessView(LoggedCallMixin, APIView):
    parser_classes = (JSONParser,)
    permission_classes = (ManagerPermission,)

    def post(self, request, tag_type, tag_id):
        ChangeTagsAccess(tag_type, tag_id).save(request.data)
        return Response({})

    def get(self, request, tag_type, tag_id):
        assert request.user.role == USER_ROLES[2][0]
        return Response(ChangeTagsAccess(tag_type, tag_id).data)


class UploadTagsView(LoggedCallMixin, APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = (ManagerPermission,)

    def post(self, request, tag_type):
        if 'file' not in request.data:
            raise exceptions.APIException(_('The file with tags was not provided'))
        UploadTags(request.user, tag_type, request.data['file'])
        return Response({})


class RemoveVersionsBase(LoggedCallMixin, DestroyAPIView):
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        mark = self.get_object()
        access = MarkAccess(request.user, mark=mark)
        if not access.can_edit:
            raise exceptions.ValidationError(_("You don't have an access to edit this mark"))

        checked_versions = mark.versions.filter(version__in=json.loads(request.data['versions']))
        for mark_version in checked_versions:
            if not access.can_remove_version(mark_version):
                raise exceptions.ValidationError(_("You don't have an access to remove one of the selected version"))
        if len(checked_versions) == 0:
            raise exceptions.ValidationError(_('There is nothing to delete'))
        checked_versions.delete()

        return Response({'message': _('Selected versions were successfully deleted')})


class SafeRmVersionsView(RemoveVersionsBase):
    queryset = MarkSafe.objects


class UnsafeRmVersionsView(RemoveVersionsBase):
    queryset = MarkUnsafe.objects


class UnknownRmVersionsView(RemoveVersionsBase):
    queryset = MarkUnknown.objects


class CheckUnknownFuncView(LoggedCallMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, report_id):
        res = CheckUnknownFunction(
            get_object_or_404(ReportUnknown, pk=report_id),
            request.data['function'],
            request.data['problem_pattern'],
            request.data['is_regex']
        )
        return Response(data={
            'result': res.match, 'problem': res.problem, 'matched': int(res.problem is not None)
        })


class RemoveSafeMarksView(LoggedCallMixin, APIView):
    unparallel = [MarkSafe]
    permission_classes = (ManagerPermission,)

    def delete(self, request):
        remove_safe_marks(id__in=json.loads(self.request.POST['ids']))
        return Response(status=status.HTTP_204_NO_CONTENT)


class RemoveUnsafeMarksView(LoggedCallMixin, APIView):
    unparallel = [MarkUnsafe]
    permission_classes = (ManagerPermission,)

    def delete(self, request):
        remove_unsafe_marks(id__in=json.loads(self.request.POST['ids']))
        return Response(status=status.HTTP_204_NO_CONTENT)


class RemoveUnknownMarksView(LoggedCallMixin, APIView):
    unparallel = [MarkUnknown]
    permission_classes = (ManagerPermission,)

    def delete(self, request):
        remove_unknown_marks(id__in=json.loads(self.request.POST['ids']))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfirmSafeMarkView(LoggedCallMixin, APIView):
    def post(self, request, pk):
        confirm_safe_mark(request.user, get_object_or_404(MarkSafeReport, pk=pk))
        return Response({})

    def delete(self, request, pk):
        unconfirm_safe_mark(request.user, get_object_or_404(MarkSafeReport, pk=pk))
        return Response({})


class ConfirmUnsafeMarkView(LoggedCallMixin, APIView):
    def post(self, request, pk):
        confirm_unsafe_mark(request.user, get_object_or_404(MarkUnsafeReport, pk=pk))
        return Response({})

    def delete(self, request, pk):
        unconfirm_unsafe_mark(request.user, get_object_or_404(MarkUnsafeReport, pk=pk))
        return Response({})


class ConfirmUnknownMarkView(LoggedCallMixin, APIView):
    def post(self, request, pk):
        confirm_unknown_mark(request.user, get_object_or_404(MarkUnknownReport, pk=pk))
        return Response({})

    def delete(self, request, pk):
        unconfirm_unknown_mark(request.user, get_object_or_404(MarkUnknownReport, pk=pk))
        return Response({})


class LikeMarkBase(LoggedCallMixin, APIView):
    association_model = None
    like_model = None

    def process_like(self, pk, user, dislike):
        assert self.association_model is not None and self.like_model is not None, 'Wrong usage'
        association = get_object_or_404(self.association_model, pk=pk)
        self.like_model.objects.filter(association=association, author=user).delete()
        self.like_model.objects.create(association=association, author=user, dislike=dislike)

    def post(self, request, pk):
        self.process_like(pk, request.user, False)
        return Response({})

    def delete(self, request, pk):
        self.process_like(pk, request.user, True)
        return Response({})


class LikeSafeMark(LikeMarkBase):
    association_model = MarkSafeReport
    like_model = SafeAssociationLike


class LikeUnsafeMark(LikeMarkBase):
    association_model = MarkUnsafeReport
    like_model = UnsafeAssociationLike


class LikeUnknownMark(LikeMarkBase):
    association_model = MarkUnknownReport
    like_model = UnknownAssociationLike

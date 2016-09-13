#
# Copyright (c) 2014-2016 ISPRAS (http://www.ispras.ru)
# Institute for System Programming of the Russian Academy of Sciences
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import re

from core.avtg.emg.common.signature import Declaration, Pointer, Structure, Array, Union, Function, Primitive, \
    import_declaration


class CModel:

    def __init__(self, logger, conf, files, entry_point_name, entry_file):
        self.entry_point_file = entry_file
        self.entry_point_name = entry_point_name
        self._logger = logger
        self._conf = conf
        self._files = files
        self._variables = dict()
        self._functions = dict()
        self._before_aspects = dict()

    def add_before_aspect(self, code, file=None):
        # Prepare code
        body = ['before: file ("$this")\n']
        body.extend(code)
        body.append('}\n')

        if file:
            files = [self._before_aspects[file].append(code)]
        else:
            files = self._files

        # Add code
        map(lambda f: self._before_aspects[f].append(code), files)

        return

    def propogate_aux_function(self, analysis, automaton, function):
        # Determine files to export
        files = set()
        if automaton.process.category == "kernel models":
            # Calls
            function_obj = analysis.get_kernel_function(automaton.process.name)
            files.update(set(function_obj.files_called_at))
            for caller in (c for c in function_obj.functions_called_at):
                # Caller definitions
                files.update(set(analysis.get_modules_function_files(caller)))

        # Export
        for file in files:
            self._add_function_declaration(file, function, extern=True)

    def add_function_definition(self, file, function):
        if file not in self.files:
            self.files[file] = {
                'variables': {},
                'functions': {},
                'declarations': {},
                'initializations': {}
            }

        if self.entry_file not in self.files:
            self.files[self.entry_file] = {
                'variables': {},
                'functions': {},
                'declarations': {},
                'initializations': {}
            }

        self.files[file]['functions'][function.name] = function.get_definition()
        self._add_function_declaration(file, function, extern=False)

class Variable:
    name_re = re.compile("\(?\*?%s\)?")

    def __init__(self, name, file, signature, export=False):
        self.name = name
        self.file = file
        self.export = export
        self.value = None
        self.use = 0

        if type(signature) is str:
            self.declaration = import_declaration(signature)
        elif issubclass(type(signature), Declaration):
            self.declaration = signature
        else:
            raise ValueError("Attempt to create variable {} without signature".format(name))

    def declare_with_init(self):
        # Ger declaration
        declaration = self.declare(extern=False)

        # Add memory allocation
        if self.value:
            declaration += " = {}".format(self.value)

        return declaration

    def declare(self, extern=False):
        # Generate declaration
        expr = self.declaration.to_string(self.name)

        # Add extern prefix
        if extern:
            expr = "extern " + expr

        return expr


class FunctionDefinition:

    def __init__(self, name, file, signature=None, export=False):
        self.name = name
        self.file = file
        self.export = export
        self.body = []

        if not signature:
            signature = 'void f(void)'
        self.declaration = import_declaration(signature)

    def get_declaration(self, extern=False):
        declaration = self.declaration.to_string(self.name)
        declaration += ';'

        if extern:
            declaration = "extern " + declaration
        return [declaration + "\n"]

    def get_definition(self):
        declaration = '{} {}({})'.format(self.declaration.return_value.to_string(), self.name,
                                         ', '.join([self.declaration.parameters[index].to_string('arg{}'.format(index))
                                                    for index in range(len(self.declaration.parameters))]))

        lines = list()
        lines.append(declaration + " {\n")
        lines.extend(['\t{}\n'.format(stm) for stm in self.body])
        lines.append("}\n")
        return lines


class Aspect(FunctionDefinition):

    def __init__(self, name, declaration, aspect_type="after"):
        self.name = name
        self.declaration = declaration
        self.aspect_type = aspect_type
        self.body = []

    def get_aspect(self):
        lines = list()
        lines.append("after: call({}) ".format("$ {}(..)".format(self.name)) +
                     " {\n")
        lines.extend(['\t{}\n'.format(stm) for stm in self.body])
        lines.append("}\n")
        return lines


class FunctionModels:

    def __init__(self, translation_conf=dict()):
        self.use_sizeof = False
        if 'allocate with sizeof' in translation_conf and translation_conf['allocate with sizeof']:
            self.use_sizeof = True

    mem_function_map = {
        # TODO: switch to correct memory allocation function when sizes will be known.
        "ALLOC": "ldv_xmalloc",
        "UALLOC": "ldv_xmalloc_unknown_size",
        "ZALLOC": "ldv_zalloc"
    }
    free_function_map = {
        "FREE": "ldv_free"
    }
    irq_function_map = {
        "IN_INTERRUPT_CONTEXT": 'ldv_in_interrupt_context',
        "SWITCH_TO_IRQ_CONTEXT": 'ldv_switch_to_interrupt_context',
        "SWITCH_TO_PROCESS_CONTEXT": 'ldv_switch_to_process_context'
    }

    mem_function_template = "\$({})\(%({})%(?:,\s?(\w+))?\)"
    simple_function_template = "\$({})\("
    access_template = '\w+(?:(?:[.]|->)\w+)*'
    mem_function_re = re.compile(mem_function_template.format('\w+', access_template))
    simple_function_re = re.compile(simple_function_template.format('\w+'))
    access_re = re.compile('(%{}%)'.format(access_template))

    def init_pointer(self, signature):
        if self.use_sizeof:
            return "{}(sizeof({}))".format(self.mem_function_map["ALLOC"], signature.points.to_string(''))
        else:
            return "{}(sizeof({}))".format(self.mem_function_map["ALLOC"], '0')

    def text_processor(self, automaton, statement):
        # Replace function names
        stms = []
        matched = False
        for fn in self.simple_function_re.findall(statement):
            matched = True

            # Bracket is required to ignore CIF expressions like $res or $arg1
            if fn in self.mem_function_map or fn in self.free_function_map:
                access = self.mem_function_re.search(statement).group(2)
                if fn in self.mem_function_map:
                    replacement = self._replace_mem_call
                else:
                    replacement = self._replace_free_call

                accesses = automaton.process.resolve_access('%{}%'.format(access))
                for access in accesses:
                    ualloc_flag = True
                    if access.interface:
                        if access.interface.manually_specified:
                            ualloc_flag = False
                        signature = access.label.get_declaration(access.interface.identifier)
                    else:
                        signature = access.label.prior_signature

                    if signature:
                        if access.interface:
                            var = automaton.determine_variable(access.label, access.list_interface[0].identifier)
                        else:
                            var = automaton.determine_variable(access.label)

                        if type(var.declaration) is Pointer:
                            self.signature = var.declaration
                            self.ualloc_flag = ualloc_flag
                            new = self.mem_function_re.sub(replacement, statement)
                            new = access.replace_with_variable(new, var)
                            stms.append(new)
            elif fn in self.irq_function_map:
                statement = self.simple_function_re.sub(self.irq_function_map[fn] + '(', statement)
                stms.append(statement)
            else:
                raise NotImplementedError("Model function '${}' is not supported".format(fn))

        if not matched:
            stms = [statement]

        # Replace rest accesses
        final = []
        for original_stm in stms:
            # Collect dublicates
            stm_set = {original_stm}

            while len(stm_set) > 0:
                stm = stm_set.pop()

                if self.access_re.search(stm):
                    expression = self.access_re.search(stm).group(1)
                    accesses = automaton.process.resolve_access(expression)
                    for access in accesses:
                        if access.interface:
                            var = automaton.determine_variable(access.label, access.list_interface[0].identifier)
                        else:
                            var = automaton.determine_variable(access.label)

                        stm = access.replace_with_variable(stm, var)
                        stm_set.add(stm)
                else:
                    final.append(stm)

        return final

    def _replace_mem_call(self, match):
        function, label_name, flag = match.groups()
        size = '0'

        if function not in self.mem_function_map:
            raise NotImplementedError("Model of {} is not supported".format(function))
        elif not self.mem_function_map[function]:
            raise NotImplementedError("Set implementation for the function {}".format(function))

        if type(self.signature) is Pointer:
            if function == 'ALLOC' and self.ualloc_flag:
                # Do not alloc memory anyway for unknown resources anyway to avoid incomplete type errors
                function = 'UALLOC'
            if function != 'UALLOC' and self.use_sizeof:
                size = 'sizeof({})'.format(self.signature.points.to_string(''))

            return "{}({})".format(self.mem_function_map[function], size)
        else:
            raise ValueError('This is not a pointer')

    def _replace_free_call(self, match):
        function, label_name, flag = match.groups()
        if function not in self.free_function_map:
            raise NotImplementedError("Model of {} is not supported".format(function))
        elif not self.free_function_map[function]:
            raise NotImplementedError("Set implementation for the function {}".format(function))

        # Create function call
        if type(self.signature) is Pointer:
            return "{}(%{}%)".format(self.free_function_map[function], label_name)
        else:
            raise ValueError('This is not a pointer')

__author__ = 'Ilja Zakharov <ilja.zakharov@ispras.ru>'

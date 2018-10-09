#
# Copyright (c) 2018 ISP RAS (http://www.ispras.ru)
# Ivannikov Institute for System Programming of the Russian Academy of Sciences
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

import os
import zipfile
import importlib
import clade.interface as clade_api

import core.components
import core.utils


class VOG(core.components.Component):

    VO_FILE = 'verification_objects.json'

    def generate_verification_objects(self):
        # Collect and merge configuration
        fragdb = self.conf['program fragmentation DB']

        # Import clade
        clade_api.setup(self.conf['build base'])

        # Make basic sanity checks and merge configurations
        desc = self._merge_configurations(fragdb, self.conf['program'], self.conf['version'],
                                          self.conf['fragmentation set'])

        # Import project strategy
        program = desc.get('program')
        if not program:
            raise KeyError('There is no available supported program fragmentation template {!r}, the following are '
                           'available: {}'.format(program, ' ,'.join(fragdb['templates'].keys())))
        strategy = self._get_fragmentation_strategy(program)

        # Fragmentation
        strategy = strategy(self.logger, self.conf, desc, clade_api)
        attr_data, fragments_files = strategy.fragmentation()

        # Prepare attributes
        self.source_paths = strategy.source_paths
        self.submit_project_attrs(*attr_data)

        self.prepare_descriptions_file(fragments_files)
        self.clean_dir = True
        self.excluded_clean = [d for d in strategy.dynamic_excluded_clean]
        self.logger.debug("Excluded {0}".format(self.excluded_clean))

    main = generate_verification_objects

    def submit_project_attrs(self, attrs, dfiles):
        """Has a callback!"""
        with open('data attributes.zip', mode='w+b', buffering=0) as f:
            with zipfile.ZipFile(f, mode='w', compression=zipfile.ZIP_DEFLATED) as zfp:
                for df in dfiles:
                    zfp.write(df)
                os.fsync(zfp.fp)
        core.utils.report(self.logger,
                          'attrs',
                          {
                              'id': self.id,
                              'attrs': attrs,
                              'attr data': 'data attributes.zip'
                          },
                          self.mqs['report files'],
                          self.vals['report id'],
                          self.conf['main working directory'])

    def prepare_descriptions_file(self, files):
        """Has a callback!"""
        # Add dir to exlcuded from cleaning by lkvog
        for file in files:
            root_dir_id = file.split('/')[0]
            if root_dir_id not in self.dynamic_excluded_clean:
                self.logger.debug("Do not clean dir {!r} on component termination".format(root_dir_id))
                self.dynamic_excluded_clean.append(root_dir_id)

        with open(self.VO_FILE, 'w') as fp:
            fp.writelines((os.path.relpath(f, self.conf['main working directory']) + '\n' for f in files))

    def _merge_configurations(self, db, program, version, dset):
        self.logger.info("Search for fragmentation description and configuration for {!r}".format(program))

        # Basic sanity checks
        if not db.get('fragmentation') or db.get('templates'):
            raise KeyError("Provide both 'templates' and 'fragmentation sets' sections to 'program configuration'.json")

        desc = db['fragmentation sets'].get(dset).get(version)
        if not desc and not db['templates'].get(dset):
            raise KeyError('There is no prepared fragmentation set {!r} for program {!r} of version {!r}'.
                           format(dset, program, version))

        # Merge templates
        template = db['templates'][dset]
        do = [template]
        while do:
            tmplt = do.pop()
            template.update(tmplt)
            if tmplt.get('template'):
                if db['templates'].get(tmplt.get('template')):
                    do.append(db['templates'].get(tmplt.get('template')))
                    del template['template']
                else:
                    raise KeyError("There is no template {!r} in program fragmentation file".
                                   format(tmplt.get('template')))

        # Merge template and fragmentation set
        desc.update(template)

        return template

    def _get_fragmentation_strategy(self, strategy_name):
        self.logger.info('Import fragmentation strategy {!r}'.format(strategy_name))
        module_path = '.vog.fragmentation.{}'.format(strategy_name.lower())
        project_package = importlib.import_module(module_path, 'core')
        cls = getattr(project_package, strategy_name.capitalize())
        return cls

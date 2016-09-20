/*
 * Copyright (c) 2014-2016 ISPRAS (http://www.ispras.ru)
 * Institute for System Programming of the Russian Academy of Sciences
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * ee the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <linux/module.h>
#include <linux/device.h>
#include <scsi/scsi_host.h>
#include <linux/emg/test_model.h>
#include <verifier/nondet.h>

struct device *dev;
struct Scsi_Host *host;

static int ldv_reset(struct scsi_cmnd *cmd){
	ldv_invoke_reached();
	return 0;
}

static struct scsi_host_template ldv_template = {
	.eh_bus_reset_handler   = ldv_reset,
};

static int __init ldv_init(void)
{
	host = scsi_host_alloc(&ldv_template, sizeof(void *));
	if (host) {
		ldv_register();
		return scsi_add_host(host, dev);
	}
	else
		return -ENOMEM;
}

static void __exit ldv_exit(void)
{
	scsi_unregister(host);
}

module_init(ldv_init);
module_exit(ldv_exit);

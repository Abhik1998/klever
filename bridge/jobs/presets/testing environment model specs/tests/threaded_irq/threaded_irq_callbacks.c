#include <linux/module.h>
#include <linux/interrupt.h>
#include <linux/irqreturn.h>
#include <linux/emg/test_model.h>
#include <verifier/nondet.h>

unsigned int irq_id = 100;
void * data;
int flip_a_coin;

static irqreturn_t irq_handler(int irq_id, void * data)
{
	ldv_invoke_callback();
	ldv_probe_up();
	return IRQ_WAKE_THREAD;
}

static irqreturn_t ldv_thread(int irq_id, void * data)
{
	ldv_release_down();
    ldv_invoke_callback();
	return IRQ_HANDLED;
}

static int __init ldv_init(void)
{
	flip_a_coin = ldv_undef_int();
    if (flip_a_coin) {
        ldv_register();
        return request_threaded_irq(irq_id, irq_handler, ldv_thread, 0, "ldv interrupt", data);
    }
    return 0;
}

static void __exit ldv_exit(void)
{
	if (flip_a_coin) {
        free_irq(irq_id, data);
        ldv_deregister();
    }
}

module_init(ldv_init);
module_exit(ldv_exit);

#include <linux/module.h>
#include <linux/genhd.h>

int __init my_init(void)
{
	int minors;
	struct gendisk *disk;

	disk = alloc_disk(minors);
	if (!disk)
	    return -1;
	add_disk(disk);
	del_gendisk(disk);
	add_disk(disk);
	del_gendisk(disk);
	put_disk(disk);
	disk = alloc_disk(minors);
	if (!disk)
	    return -1;
	add_disk(disk);
	del_gendisk(disk);
	add_disk(disk);
	del_gendisk(disk);
	put_disk(disk);

	return 0;
}

module_init(my_init);
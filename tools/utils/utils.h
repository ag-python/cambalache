#include <gtk/gtk.h>

GParamSpec **cmb_utils_get_iface_properties(const gchar *name);

gboolean cmb_utils_implements_buildable_add_child(GObject *buildable);

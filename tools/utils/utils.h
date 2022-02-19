#include <gtk/gtk.h>

GParamSpec **cmb_utils_get_class_properties(const gchar *name);
GParamSpec **cmb_utils_get_iface_properties(const gchar *name);

gboolean cmb_utils_implements_buildable_add_child(GObject *buildable);

const gchar *cmb_utils_pspec_enum_get_default_nick (GType gtype, gint default_value);

gchar *cmb_utils_pspec_flags_get_default_nick (GType gtype, guint default_value);

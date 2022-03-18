#include <gtk/gtk.h>

void
cmb_private_object_set_property_from_string (GObject *object,
                                             const gchar *property_name,
                                             const gchar *value);

#if GTK_MAJOR_VERSION == 3
void
cmb_private_container_child_set_property_from_string (GtkContainer *container,
                                                      GtkWidget    *child,
                                                      const gchar  *property_name,
                                                      const gchar  *value);
#endif

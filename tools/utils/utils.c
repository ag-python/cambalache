#include <utils.h>

 /**
  * cmb_utils_get_iface_properties:
  * @name: Interface type name
  *
  * Return the list of properties decalred in @name iface
  *
  * Returns: (array zero-terminated=1) (element-type GParamSpec) (transfer container): iface properties
  */
GParamSpec **
cmb_utils_get_iface_properties(const gchar *name)
{
  GType gtype = g_type_from_name(name);
  gpointer iface = g_type_default_interface_ref(gtype);
  return g_object_interface_list_properties(iface, NULL);
}

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

/**
 * cmb_utils_implements_buildable_add_child:
 * @buildable: Object to check if it has an iface
 *
 * Return wheter buildable implements add_child() or not
 *
 */
gboolean
cmb_utils_implements_buildable_add_child(GObject *buildable)
{
  GtkBuildableIface *iface = NULL;

  if (!GTK_IS_BUILDABLE(buildable))
    return FALSE;

  iface = GTK_BUILDABLE_GET_IFACE(buildable);
  while (iface)
    {
      if (iface->add_child != NULL)
        return TRUE;

      iface = g_type_interface_peek_parent(iface);
    }

  return FALSE;
}

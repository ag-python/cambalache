#include <utils.h>

/**
 * cmb_utils_get_class_properties:
 * @name: Class name
 *
 * Return the list of properties declared in @name
 *
 * Returns: (array zero-terminated=1) (element-type GParamSpec) (transfer container): class properties
 */
GParamSpec **
cmb_utils_get_class_properties(const gchar *name)
{
  GtkBuilder *builder = gtk_builder_new ();
  GType gtype = gtk_builder_get_type_from_name(builder, name);
  gpointer oclass = NULL;

  g_object_unref(builder);
  oclass = g_type_class_ref(gtype);

  return g_object_class_list_properties(oclass, NULL);
}


/**
 * cmb_utils_get_iface_properties:
 * @name: Interface type name
 *
 * Return the list of properties declared in @name iface
 *
 * Returns: (array zero-terminated=1) (element-type GParamSpec) (transfer container): iface properties
 */
GParamSpec **
cmb_utils_get_iface_properties(const gchar *name)
{
  GType gtype = g_type_from_name(name);
  gpointer iface = NULL;

  g_type_ensure(gtype);
  iface = g_type_default_interface_ref(gtype);

  return g_object_interface_list_properties(iface, NULL);
}

/**
 * cmb_utils_implements_buildable_add_child:
 * @name: Object class name to check
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

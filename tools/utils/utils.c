/*
 * Copyright (C) 2021 Juan Pablo Ugarte.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; version 2 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Authors:
 *   Juan Pablo Ugarte <juanpablougarte@gmail.com>
 */

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
 * @buildable: Object to check
 *
 * Return whether buildable implements add_child() or not
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

/**
 * cmb_utils_pspec_enum_get_default_nick:
 * @gtype:
 * @default_value:
 *
 *
 */
const gchar *
cmb_utils_pspec_enum_get_default_nick(GType gtype, gint default_value)
{
  GEnumClass *enum_class = g_type_class_ref (gtype);;
  GEnumValue *enum_value= g_enum_get_value (enum_class, default_value);
  const gchar *retval = NULL;

  if (enum_value)
    retval = enum_value->value_nick;

  g_type_class_unref (enum_class);

  return retval;
}

/**
 * cmb_utils_pspec_flags_get_default_nick:
 * @gtype:
 * @default_value:
 *
 *
 */
gchar *
cmb_utils_pspec_flags_get_default_nick(GType gtype, guint default_value)
{
  GFlagsClass *flags_class = g_type_class_ref (gtype);
  GFlagsValue *flags_value = NULL;
  GString *str = g_string_new("");

  do {
    flags_value = g_flags_get_first_value (flags_class, default_value);

    if (flags_value) {
      if (flags_value->value == 0) break;

      if (str->len)
        g_string_append (str, " | ");

      g_string_append (str, flags_value->value_nick);

      /* Remove first value bit */
      default_value &= ~flags_value->value;
    }

  } while (flags_value);

  g_type_class_unref (flags_class);

  if (str->len)
    return g_string_free(str, FALSE);

  g_string_free(str, TRUE);
  return NULL;
}

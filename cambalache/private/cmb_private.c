/*
 * CmbPrivate - Private utility functions
 *
 * Copyright (C) 2022 Juan Pablo Ugarte.
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

#include "cmb_private.h"

static gboolean
_value_from_string(GParamSpec *pspec, const gchar *string, GValue *value)
{
  gboolean valid = FALSE;

  if (string == NULL) {
    g_param_value_set_default (pspec, value);
    return TRUE;
  } else {
    GtkBuilder *builder = gtk_builder_new ();
    valid = gtk_builder_value_from_string (builder, pspec, string, value, NULL);
    g_object_unref (builder);
  }

  return valid;
}

/**
 * cmb_private_object_set_property_from_string:
 * @object:
 * @property_name:
 * @value: (nullable):
 *
 */
void
cmb_private_object_set_property_from_string (GObject *object,
                                             const gchar *property_name,
                                             const gchar *value)
{
  GParamSpec *pspec = g_object_class_find_property (G_OBJECT_GET_CLASS(object), property_name);
  GValue gvalue = G_VALUE_INIT;

  if (pspec == NULL)
    return;

  if (_value_from_string(pspec, value, &gvalue)) {
    g_object_set_property (object, property_name, &gvalue);
    g_value_unset (&gvalue);
  }
}

#if GTK_MAJOR_VERSION == 3

/**
 * cmb_private_container_child_set_property_from_string:
 * @container:
 * @child:
 * @property_name:
 * @value: (nullable):
 *
 */
void
cmb_private_container_child_set_property_from_string (GtkContainer *container,
                                                      GtkWidget    *child,
                                                      const gchar  *property_name,
                                                      const gchar  *value)
{
  GParamSpec *pspec = gtk_container_class_find_child_property (G_OBJECT_GET_CLASS(container), property_name);
  GValue gvalue = G_VALUE_INIT;

  if (pspec == NULL)
    return;

  if (_value_from_string(pspec, value, &gvalue)) {
    gtk_container_child_set_property (container, child, property_name, &gvalue);
    g_value_unset (&gvalue);
  }
}

#endif

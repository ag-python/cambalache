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
  static GtkBuilder *builder = NULL;

  if (string == NULL) {
    g_param_value_set_default (pspec, value);
    return TRUE;
  }

  if (builder == NULL)
    builder = gtk_builder_new ();

  return gtk_builder_value_from_string (builder, pspec, string, value, NULL);
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

#if GTK_MAJOR_VERSION == 4

struct _CmbPrivateBuilderScope
{
  GtkBuilderCScope  parent_instance;
};

static GtkBuilderScopeInterface *parent_iface;

static void cmb_private_builder_scope_scope_init (GtkBuilderScopeInterface *iface);

G_DEFINE_TYPE_WITH_CODE (CmbPrivateBuilderScope, cmb_private_builder_scope, GTK_TYPE_BUILDER_CSCOPE,
                         G_IMPLEMENT_INTERFACE (GTK_TYPE_BUILDER_SCOPE,
                                                cmb_private_builder_scope_scope_init))

static GType
cmb_private_builder_scope_get_type_from_name (GtkBuilderScope *scope,
                                              GtkBuilder      *builder,
                                              const char      *type_name)
{
  g_autofree gchar *mrg_type_name = g_strconcat("Merengue", type_name, NULL);
  GType mrg_type;

  if ((mrg_type = g_type_from_name (mrg_type_name)) != G_TYPE_INVALID)
    return mrg_type;

  return parent_iface->get_type_from_name (scope, builder, type_name);
}

static void
cmb_private_builder_scope_class_init (CmbPrivateBuilderScopeClass *klass)
{
}

static void
cmb_private_builder_scope_scope_init (GtkBuilderScopeInterface *iface)
{
  parent_iface = g_type_interface_peek_parent (iface);
  iface->get_type_from_name = cmb_private_builder_scope_get_type_from_name;
}

static void
cmb_private_builder_scope_init (CmbPrivateBuilderScope *self)
{
}

#else

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

/*
 * Workaround:
 *
 * GtkBuilder can not be subclassed so there is no clean way to override
 * get_type_from_name()
 *
 */

typedef GType (*getType) (GtkBuilder *, const char *);

struct _MrgBuilderClass
{
  GObjectClass parent_class;

  GType (* get_type_from_name) (GtkBuilder *builder,
                                const char *type_name);

  /* Padding for future expansion */
  void (*_gtk_reserved1) (void);
  void (*_gtk_reserved2) (void);
  void (*_gtk_reserved3) (void);
  void (*_gtk_reserved4) (void);
  void (*_gtk_reserved5) (void);
  void (*_gtk_reserved6) (void);
  void (*_gtk_reserved7) (void);
  void (*_gtk_reserved8) (void);
};

typedef struct _MrgBuilderClass MrgBuilderClass;

static getType __get_type_from_name = NULL;

static GType
_get_type_from_name (GtkBuilder *builder, const char *type_name)
{
  g_autofree gchar *mrg_type_name = g_strconcat("Merengue", type_name, NULL);
  GType mrg_type;

  if ((mrg_type = g_type_from_name (mrg_type_name)) != G_TYPE_INVALID)
    return mrg_type;

  return __get_type_from_name  (builder, type_name);
}

/**
 * cmb_private_builder_init:
 *
 */
void
cmb_private_builder_init ()
{
  MrgBuilderClass *klass;

  if (__get_type_from_name)
    return;

  /* Ensure GtkBuilder is registered */
  g_type_ensure (GTK_TYPE_BUILDER);

  /* Get Class pointer */
  klass = g_type_class_ref (GTK_TYPE_BUILDER);

  if (!klass)
    return;

  __get_type_from_name = klass->get_type_from_name;

  /* Monkey patch */
  klass->get_type_from_name = _get_type_from_name;
}

#endif

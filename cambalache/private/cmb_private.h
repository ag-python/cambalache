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

#ifndef __CMB_PRIVATE_H__
#define __CMB_PRIVATE_H__

#include <gtk/gtk.h>

G_BEGIN_DECLS

#if GTK_MAJOR_VERSION == 4

#define CMB_PRIVATE_TYPE_BUILDER_SCOPE (cmb_private_builder_scope_get_type())

G_DECLARE_FINAL_TYPE (CmbPrivateBuilderScope, cmb_private_builder_scope, CMB_PRIVATE, BUILDER_SCOPE, GtkBuilderCScope)

#else

void
cmb_private_container_child_set_property_from_string (GtkContainer *container,
                                                      GtkWidget    *child,
                                                      const gchar  *property_name,
                                                      const gchar  *value);


void cmb_private_builder_init (void);

#endif

void
cmb_private_object_set_property_from_string (GObject *object,
                                             const gchar *property_name,
                                             const gchar *value);

G_END_DECLS

#endif

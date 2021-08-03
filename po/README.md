# Localisation

Cambalache uses gettext for translations.

See [meson docs](https://mesonbuild.com/Localisation.html) for more details.

### Adding a new language

 - Add the language code to LINGUAS file
 - Update the .po files
 - Translate .po file (You can use gtranslator gui)
 - Create MR in gitlab

### Updating .po files

Each time new strings are added to the project we need to update the .po file

`meson compile cambalache-update-po`
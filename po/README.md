# Localisation

Cambalache uses gettext for translations.

See [meson docs](https://mesonbuild.com/Localisation.html) for more details.

Until we have an automated workflow for translations updating the po file should
be done by the first translator that works on it.
This way we avoid having a commit for each time we add or change a string and
only have one when we actually have new translations.

I (Juan Pablo) will try to keep the spanish translation up to date, so other translators
can use it as a cue for when it is a good time to translate.

thanks!

### Adding a new language

 - Add the language code to LINGUAS file
 - Update the .po files
 - Translate .po file (You can use gtranslator gui)
 - Create MR in gitlab

### Updating .po files

Each time new strings are added to the project we need to update the .po file

```
mkdir _build
cd _build
meson
meson compile cambalache-update-po
```


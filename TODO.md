## Project:
 
 - Templates

 - CSS
 
 - GResource


## GtkBuilder missing features:
 
 - Special type children
   - <child type=""> 
 
 - Internal children
   - <child internal-child="name">
 
 - Properties
   - Translatable parameter
   - Bindings
 
 - GMenuModel
   <menu id="">
    <section>
      <item>
        <attribute name="" translatable="yes">Value</attribute>
      </item>
    </section>
    <section>
      <submenu>
        <attribute name="" translatable="yes">Value</attribute>
        <section/>
      </submenu>
    </section>
  </menu>
 
 - GtkWidget
   - <style> <class name="css-class"/> </style>
   -  <action-widgets>
        <action-widget response="cancel">cancel_info_dialog</action-widget>
      </action-widgets>

 - GtkListStore
   - <columns> <column type=""/> </columns>
   - <data> <row> <col id="0">value</col> </row> </data>

 - GtkTreeStore
   - <columns> <column type=""/> </columns>

 - GtkCellRendererText
   - <attributes> <attribute name="text">0</attribute> </attributes>

 - GtkLevelBar
   - <offsets> <offset name="low" value="1"/> </offsets>

 - GtkScale
   - <marks> <mark value="0" position="bottom"> </mark>

 - GtkComboBoxText
   - <items> <item>1</item> </items>
   
 - GtkSizeGroup
   - <widgets> <widget name="listboxrow1"/> </widgets>

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
   - <action-widgets>
       <action-widget response="">value</action-widget>
     </action-widgets>

 - GtkListStore
   - <columns> <column type="gtype"/> </columns>
   - <data> <row> <col id="int">value</col> </row> </data>

 - GtkTreeStore
   - <columns> <column type="gtype"/> </columns>

 - GtkLabel
   - <attributes> <attribute name="gchararray" value="red" start="5" end="10">int</attribute> </attributes>

 - GtkLevelBar
   - <offsets> <offset name="gchararray" value="1"/> </offsets>

 - GtkScale
   - <marks> <mark value="0" position="bottom"> </mark>

 - GtkComboBoxText
   - <items> <item>1</item> </items>
   
 - GtkSizeGroup
   - <widgets> <widget name="gchararray"/> </widgets>

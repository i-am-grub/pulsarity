User Interface
===============

The Pulsarity user Interface can be extended through the built in
element tree interface. The element tree (otherwise known as etree)
is the core component of plugin defined user interface extendability.
The design of the api interface maps an 
to a specific page within the user interface; additional elements
defined in the user interface plugin api can then be mapped onto the
defined element tree.

The following user interface elements are currently supported:

+---------------------+-----------------------------------------------+
| Element Type        | Class                                         |
+=====================+===============================================+
| Page                | :py:class:`~pulsarity.api.ui.UIPage`          |
+---------------------+-----------------------------------------------+
| Element Tree        | :py:class:`~pulsarity.api.ui.UIETree`         |
+---------------------+-----------------------------------------------+
| Markdown Field      | :py:class:`~pulsarity.api.ui.UIMarkdownField` |
+---------------------+-----------------------------------------------+
| Button Field        | :py:class:`~pulsarity.api.ui.UIButtonField`   |
+---------------------+-----------------------------------------------+
| Value Field         | (See table below)                             |
+---------------------+-----------------------------------------------+

Value fields are based on HTML input types. The following are currently
supported: 

+---------------------+--------------------------------------------------------+
| Value Field Types   | Class                                                  |
+=====================+========================================================+
| Checkbox            | :py:class:`~pulsarity.api.ui.UICheckboxValueField`     |
+---------------------+--------------------------------------------------------+
| Datetime            | :py:class:`~pulsarity.api.ui.UIDatetimeValueField`     |
+---------------------+--------------------------------------------------------+
| Date                | :py:class:`~pulsarity.api.ui.UIDateValueField`         |
+---------------------+--------------------------------------------------------+
| Email               | :py:class:`~pulsarity.api.ui.UIEmailValueField`        |
+---------------------+--------------------------------------------------------+
| Number              | :py:class:`~pulsarity.api.ui.UINumberValueField`       |
+---------------------+--------------------------------------------------------+
| Password            | :py:class:`~pulsarity.api.ui.UIPasswordValueField`     |
+---------------------+--------------------------------------------------------+
| Range               | :py:class:`~pulsarity.api.ui.UIRangeValueField`        |
+---------------------+--------------------------------------------------------+
| Select              | :py:class:`~pulsarity.api.ui.UISelectValueField`       |
+---------------------+--------------------------------------------------------+
| Telephone           | :py:class:`~pulsarity.api.ui.UITelValueField`          |
+---------------------+--------------------------------------------------------+
| Text                | :py:class:`~pulsarity.api.ui.UITextValueField`         |
+---------------------+--------------------------------------------------------+
| Time                | :py:class:`~pulsarity.api.ui.UITimeValueField`         |
+---------------------+--------------------------------------------------------+
| URL                 | :py:class:`~pulsarity.api.ui.UIURLValueField`          |
+---------------------+--------------------------------------------------------+


Element Registration
--------------------

All user interface objects must be registered before use. Each element
mush be explictly registered before it is included. Two ways to register an
user interface element are demonstrated in the following snippet:

.. code-block:: python

    from pulsarity.api.ui import UIETree

    # register an element tree with an explict function call
    tree1 = UIETree()
    tree1.register()

    # register an element tree with an explict initialization variable
    tree2 = UIETree(auto_register=True)


Element Permission
--------------------

All user interface objects can be assigned a permission that an
authenticated user is required to hold in order for the user interface
element to be rendered in the user interface. When the required
permission is held by the system's `UNAUTHENTICATED` role, elements
are visible to unauthenticated users.

.. code-block:: python

    from pulsarity.api.ui import SystemDefaultPerms, UIETree

    # Create a new tree that is only accessible to users holding the
    # the `SYSTEM_CONTROL` permission. Elements attached under this
    # tree will not be rendered for usering missing the required
    # permission
    page_tree = UIETree(permission=SystemDefaultPerms.SYSTEM_CONTROL)
    page_tree.register()



Pages
--------------------

.. code-block:: python
    
    from pulsarity.api.ui import UIPage

    # Create a new page in the admin menu
    custom_page = UIPage("my-plugin-page", parent="admin")
    custom_page.register()

    # Create a sub page of our main plugin page
    sub_custom_page = UIPage("plugin-sub-page", parent=custom_page)
    sub_custom_page.register()


Element Trees
--------------------

Element trees are the backbone of building menus from plugins. They are the glue that
map fields to specific pages (or routes) within the user interface. The element tree
can be linked to a route in the following example:

.. code-block:: python

    from pulsarity.api.ui import UIETree, UIPage

    # Create a new page in the admin menu
    custom_page = UIPage("my-plugin-page", parent="admin", auto_register=True)

    # Create a new tree that is automatically registed upon creation
    page_tree = UIETree(auto_register=True)

    # Map the tree to be attached to the custom page
    page_tree.map_to_page(custom_page)


Fields
--------------------

Fields are elements that can be attached to element trees. There are a variety
of different kinds depending on the need of the plugin - the following snippet
demonstrates adding a field to an element tree.

.. code-block:: python

    from pulsarity.api.ui import UIETree, UIMarkdownField, UIPage

    # Create a new page with an element tree in the admin menu
    custom_page = UIPage("my-plugin-page", parent="admin", auto_register=True)
    page_tree = UIETree(auto_register=True)
    page_tree.map_to_page(custom_page)

    # Create a markdown field with a heading of "Hello World"
    text = "# Hello World"
    markdown_field = UIMarkdownField(text, auto_register=True)

    # Add the markdown field to the element tree
    page_tree.add_element(markdown_field)

Fields can also be mapped to multiple element trees at once. This behavior
allows for efficient reuse of data across user interface menus.

.. code-block:: python

    from pulsarity.api.ui import UIETree, UIMarkdownField, UIPage

    # Create a new page with an element tree in the admin menu
    custom_page = UIPage("my-plugin-page-1", parent="admin", auto_register=True)
    page_1_tree = UIETree(auto_register=True)
    page_1_tree.map_to_page(custom_page)

    # Create another page with an element tree in the admin menu
    custom_page = UIPage("my-plugin-page-2", parent="admin", auto_register=True)
    page_2_tree = UIETree(auto_register=True)
    page_2_tree.map_to_page(custom_page)

    # Create a markdown field with a heading of "Hello World"
    text = "# Hello World"
    markdown_field = UIMarkdownField(text, auto_register=True)

    # Add the markdown field to the element tree 1
    page_1_tree.add_element(markdown_field)

    # Also register the element to be rendered from element tree 2
    page_2_tree.add_element(markdown_field)



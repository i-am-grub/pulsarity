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
| Markdown Renderer   | :py:class:`~pulsarity.api.ui.UIMarkdownField` |
+---------------------+-----------------------------------------------+
| Button              | :py:class:`~pulsarity.api.ui.UIButtonField`   |
+---------------------+-----------------------------------------------+
| Value Fields        | (See table below)                             |
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
mush be explictly registered before it is included.

The 

.. code-block:: python

    from pulsarity.api.ui import UIETree

    # register an element tree with an explict function call
    tree1 = UIETree()
    tree1.register()

    # register an element tree with an explict initialization variable
    tree2 = UIETree(auto_register=True)

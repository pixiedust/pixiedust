Reference
=========

@PixieApp
*********
Python class annotation to denote that a class is a PixieApp.    

@route
******
Python method annotation to denote that a method is a view. The contract is that when a method is annotated as a route, it must provide an HTML fragment for the framework to display.

The default view must have a route with no arguments e.g. `@route()`. Any other route can have multiple key-value pairs, e.g., ``@route(clicked="true", state1="foo")``. When executing a kernel request, the PixieApp dispatcher will try to find the best view match based on its route arguments according to the following rules:

- The routes with the most arguments are always evaluated first.
- All arguments must match for a route to be selected.
- If the route is not found, then the default route is selected.
- Each key of the route arguments can be either a transient state (options passed for the duration of the request) or persisted (field of the PixieApp class that remains present until explicitly changed).


**Contract for the method defined as a view:**

1. The method must provide an HTML fragment that can contain Jinja2 templating constructs (see http://jinja.pocoo.org/docs/dev/templates/ for more details on Jinja2 templating).
2. Optional: the method can have arguments that match the name of the route argument. This is useful when the route has wildcards for a particular state, and you want to use the value of this state in your code. For example:

::

    @route(state1="*", state2="*")
    def myView(self, state1, state2):
        return "<div>state1 is {}</div><div>state2 is {}</div>".format(state1, state2)

There are two ways of supplying these fragments:

1. Simply return a static string with the HTML fragment.
2. Use either ``self._addHTMLTemplate`` or ``self._addHTMLTemplateString``. Use one of these methods when you want to pass custom arguments to the Jinja2 template interpreter.

.. Note:: passing custom arguments to Jinja2 is an advanced feature that is rarely needed.
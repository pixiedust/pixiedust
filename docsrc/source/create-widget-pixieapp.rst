Creating a Widget
=================

Sometimes, you'll want to reuse complex UI constructs. In this case, you can package the HTML into a widget that can be easily called anywhere.  

- **To define a widget:** Use a route with a special ``widget`` attribute. To establish a proper binding, the value of ``pd_widget`` must match the route's widget value.

- **To invoke a widget:** Apply the pd_widget custom attribute to a <div> element and set its value to the same widget value defined in the route. For example:

::
  
  from pixiedust.display.app import *
  @PixieApp
  class TestPixieAppWidget():
      @route(widget='myWidget')
      def myWidget(self):
          return """<div><b>Hello World Widget</b></div>"""
      @route()
      def main(self):
          return """<div pd_widget="myWidget"/>"""
  
  TestPixieAppWidget().run(runInDialog='false')


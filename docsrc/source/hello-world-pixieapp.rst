Hello World PixieApp
====================

The following sample PixieApp provides two simple views and their associated routes. The first view (default view) creates a button that, when clicked, will invoke the second view. The second view creates another button that redirects to the first view, and so on and so forth. 

::


  from pixiedust.display.app import *
  @PixieApp
  class HelloWorldPixieApp:    
      @route()
      def main(self):
          return"""
              <input pd_options="clicked=true" type="button" value="Click Me">
          """    
      @route(clicked="true")
      def _clicked(self):
          return """
              <input pd_options="clicked=false" type="button" value="You Clicked, Now Go back">
          """
  #run the app
  HelloWorldPixieApp().run(runInDialog='false')

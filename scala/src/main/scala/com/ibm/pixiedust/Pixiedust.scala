/**
* Copyright IBM Corp. 2016
* 
* Licensed under the Apache License, Version 2.0 (the 'License');
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
* 
* http://www.apache.org/licenses/LICENSE-2.0
* 
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an 'AS IS' BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

package com.ibm.pixiedust

import java.io.ByteArrayOutputStream
import java.io.OutputStream
import java.util.concurrent.ConcurrentHashMap

import scala.collection.JavaConversions.mapAsScalaConcurrentMap
import scala.collection.JavaConversions.mutableMapAsJavaMap

import org.apache.toree.interpreter.ExecuteAborted
import org.apache.toree.interpreter.ExecuteError
import org.apache.toree.kernel.api.KernelLike
import org.apache.toree.kernel.interpreter.pyspark.PySparkException
import org.apache.toree.kernel.interpreter.pyspark.PySparkInterpreter
import org.apache.toree.kernel.interpreter.scala.ScalaInterpreter
import org.apache.toree.kernel.protocol.v5.MIMEType
import org.apache.toree.plugins.Plugin
import org.apache.toree.plugins.annotations.Event
import org.apache.toree.plugins.annotations.Init
import org.slf4j.LoggerFactory

import com.typesafe.config.Config
import com.typesafe.config.ConfigFactory
import com.typesafe.config.ConfigParseOptions
import com.typesafe.config.ConfigSyntax


/**
 * @author dtaieb
 * Toree plugin that makes PixieDust display and Spark Progress Monitor available via the pyspark interpreter 
 */
class Pixiedust extends Plugin{
  private val logger = LoggerFactory.getLogger(this.getClass.getName)
  
  @Init
  def init(kernel: KernelLike) = {
    logger.trace("got a kernel " + kernel)
    Pixiedust.kernel = kernel
  }
  
  @Event( name = "preRunCell")
  def preRunCell(outputStream: OutputStream){
    val code = s"""
      |from IPython.core.getipython import *
      |get_ipython().events.trigger("pre_run_cell")
      |from pixiedust.utils.sparkJobProgressMonitor import *
      |from pixiedust.utils.javaBridge import *
      |from pixiedust.utils.scalaBridge import *
      |#enableSparkJobProgressMonitor()
      |#print(get_ipython().user_ns.get("__pixiedustSparkListener")) 
    """.stripMargin
    
    Pixiedust.runPythonCode(code, Some( new Pixiedust.PixiedustOutputStream() ))
  }
  
  @Event( name = "allInterpretersReady" )
  def initPixiedust(){
    val scalaInterpreter = Pixiedust.kernel.interpreter("Scala").get.asInstanceOf[ScalaInterpreter]
    val scalaInitCode = """
      |import com.ibm.pixiedust._
      |def display(entity:Any, options: (String,Any)*){
      |  Pixiedust.display(entity, options:_*);
      |}
      |def getPixiedustLog(args:String=""){
      |  Pixiedust.getPixiedustLog(args)
      |}
      """.stripMargin
        
    logger.trace(s"Running Scala Initialization code ${scalaInitCode}");        
    scalaInterpreter.interpret(scalaInitCode, true)
    
   /*   |import logging
      |logger = logging.getLogger('py4j')
      |hdlr = logging.FileHandler('/Users/dtaieb/py4j2.log')
      |formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
      |hdlr.setFormatter(formatter)
      |logger.addHandler(hdlr) 
      |logger.setLevel(logging.DEBUG)*/
    
    val pythonInitializationCode = s"""
      |import pixiedust
      |from pixiedust.display import *
      |from pixiedust.utils.javaBridge import *
      |from pyspark.sql import *
      |sqlContext = SQLContext(sc)
      |from IPython.core.getipython import get_ipython
      |get_ipython().user_ns["sqlContext"]=sqlContext
      |pixiedust.enableJobMonitor()
    """.stripMargin
    
    Pixiedust.runPythonCode( pythonInitializationCode)
  }
}

object Pixiedust{
  private val logger = LoggerFactory.getLogger(this.getClass.getName)
  
  var kernel:KernelLike = _  
  val entities:collection.mutable.Map[String, Any] = new ConcurrentHashMap[String,Any]()
  
  def getEntity(id:String):Any={
    val entity = entities.get(id).get
    entity
  }
  
  def parse(message:String):Config={
    if (message.trim.isEmpty ){
      return null;
    }
    val options = ConfigParseOptions.defaults().setSyntax(ConfigSyntax.JSON)
    try{
      return ConfigFactory.parseString(message,options)
    }catch{
      case e:Exception => {
        return ConfigFactory.parseString(s"""{"data": {"text/plain":"${scala.util.parsing.json.JSONFormat.quoteString(message)}"}} """, options)
      }
    }
  }
  
  class PixiedustOutputStream extends OutputStream{
    override def write(b: Array[Byte], off: Int, len: Int):Unit = {
      sendContent( new String(b,off,len) )
    }
    override def write(b:Int):Unit={
      logger.error("PixiedustOutputStream::write(b:Int) should never be called")
    }
  }
  
  val pixiedustOutputStream = new PixiedustOutputStream
  
  def sendContent(msg:String):Unit = {
    logger.trace(s"processing message ${msg}")
    val payload = parse( msg )
    if (payload != null && payload.hasPath("data")){
      val data = payload.getConfig("data")
      var found = false
      val mimeTypes = Array(MIMEType.ImagePng,MIMEType.TextHtml,MIMEType.ApplicationJson,MIMEType.ApplicationJavaScript, MIMEType.PlainText)
      for (mtype <- mimeTypes){
        if (!found && data.hasPath(mtype ) ){
          found = true
          kernel.display.content( mtype, data.getString( mtype ) )
        }
      }
      
      if ( !found ){
        logger.warn(s"Unable to process message with unknown MimeType: ${msg}")
      }
    }
  }
  
  def display(entity:Any, options: (String,Any)*){    
    //Check if the entity is already an id
    var entityId:String = ""
    if (entity.isInstanceOf[String] && entities.containsKey( entity )){
      entityId = entity.asInstanceOf[String]
    }else{
      entityId = java.util.UUID.randomUUID().toString
      Pixiedust.entities.put(entityId, entity)
    }
    
    val optionsCode = if (options.length > 0) "," + options.map( a => a._1 + "='" + a._2 + "'").mkString(",") else ""
    val code = s"""
      |from pixiedust.display import *
      |from pixiedust.utils.javaBridge import *
      |def fetchEntity(entityId):
      |  entity = JavaWrapper("com.ibm.pixiedust.Pixiedust$$").getEntity(entityId) 
      |  return  ("display(\\"${entityId}\\"${optionsCode})", entity)
      |display.fetchEntity=fetchEntity
      |try:
      |  display("${entityId}"${optionsCode})
      |finally:
      |  display.fetchEntity=None
    """.stripMargin
    
    runPythonCode( code, Some(pixiedustOutputStream))
  }
  
  def getPixiedustLog(args:String=""){
    val code = s"""
      |from pixiedust.utils.pdLogging import *
      |PixiedustLoggingMagics().pixiedustLog("${args}") 
    """.stripMargin
    
    runPythonCode( code, Some(pixiedustOutputStream))
  }
  
  def runPythonCode(code:String, outputStream: Option[OutputStream] = None):Unit={    
    val pySpark = kernel.interpreter("PySpark")    
    pySpark.get match {
      case pySparkInterpreter: PySparkInterpreter =>
        val (_, output) = pySparkInterpreter.interpret(code, true, outputStream)
        output match {
          case Left(executeOutput) => logger.trace(s"Python code ${code} successfully executed")
          case Right(executeFailure) => executeFailure match {
            case executeAborted: ExecuteAborted =>
              throw new PySparkException("PySpark code was aborted!")
            case executeError: ExecuteError =>
              throw new PySparkException(executeError.value)
          }
        }
      case otherInterpreter =>
        val className = otherInterpreter.getClass.getName
        throw new PySparkException(s"Invalid PySpark interpreter: $className")
    }
  }
}



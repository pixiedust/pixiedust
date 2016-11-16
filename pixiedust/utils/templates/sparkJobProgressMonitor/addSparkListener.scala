import org.apache.spark.scheduler._
import org.apache.spark.sql.types._
import collection.JavaConverters._

def serializeStageJSON(stageInfo: StageInfo):String={
    return s"""{
        "stageId":"${stageInfo.stageId}",
        "name":"${stageInfo.name}",
        "details":"${stageInfo.details.replaceAll("\n", "\\\\\\\\n")}",
        "numTasks":${stageInfo.numTasks}
    }"""
}

def serializeStagesJSON(stageInfos: Seq[StageInfo]):String = {
    try{
        return "[" + stageInfos.map(si => serializeStageJSON(si)).reduce( _ + "," + _ ) + "]"
    }catch{
        case e:Throwable=>{
            e.printStackTrace();
            return "[]"
        }
    }
}

val __pixiedustSparkListener = new ChannelReceiver with SparkListener{    
    override def onJobStart(jobStart: SparkListenerJobStart) {
        send("jobStart", s"""{
            "jobId":"${jobStart.jobId}",
            "stageInfos":${serializeStagesJSON(jobStart.stageInfos)}
        }
        """)

        //Job started with ${jobStart.stageInfos.length} stages")
    }
    override def onJobEnd(jobEnd: SparkListenerJobEnd){
        send("jobEnd", "Job Ended")
    }
    override def onTaskStart(taskStart: SparkListenerTaskStart) { 
        send("taskStart", s"""{
            "stageId":"${taskStart.stageId}",
            "taskInfo":{
                "taskId":"${taskStart.taskInfo.taskId}", 
                "attemptNumber":${taskStart.taskInfo.attemptNumber},
                "index":${taskStart.taskInfo.index}
            }
        }
        """)

        //taskStart ${taskStart.stageId} : ${taskStart.taskInfo.taskId} : ${taskStart.taskInfo.executorId}")
    }

    override def onStageSubmitted(stageSubmitted: SparkListenerStageSubmitted) { 
        send("stageSubmitted", s"""{
            "stageInfo": ${serializeStageJSON(stageSubmitted.stageInfo)}
        }
        """)
    }

    override def onTaskEnd(taskEnd: SparkListenerTaskEnd) { 
        send("taskEnd", s"taskEnd: ${taskEnd.stageId}")
    }

    override def onTaskGettingResult(taskGettingResult: SparkListenerTaskGettingResult) { 
        send("taskGettingResult", s"taskGettingResult ${taskGettingResult.taskInfo.taskId} : ${taskGettingResult.taskInfo.executorId}")
    }

    override def onExecutorMetricsUpdate(executorMetricsUpdate: SparkListenerExecutorMetricsUpdate) { 
        //System.out.println(s"MetricsUpdate ${executorMetricsUpdate.execId} : ${executorMetricsUpdate.taskMetrics}")
    }

    override def onStageCompleted(stageCompleted: SparkListenerStageCompleted) { 
        send("stageCompleted", s"""{
            "stageInfo":${serializeStageJSON(stageCompleted.stageInfo)}
        }
        """)
        //onStageCompleted ${stageCompleted.stageInfo.name}")
    }
}

sc.addSparkListener(__pixiedustSparkListener)
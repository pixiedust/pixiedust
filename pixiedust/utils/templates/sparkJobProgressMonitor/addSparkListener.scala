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
        return "[" + stageInfos.sortWith( (s,t) => s.stageId < t.stageId ).map(si => serializeStageJSON(si)).reduce( _ + "," + _ ) + "]"
    }catch{
        case e:Throwable=>{
            e.printStackTrace();
            return "[]"
        }
    }
}

def serializeTaskJSON(taskInfo: TaskInfo):String = {
    return s"""{
        "taskId":"${taskInfo.taskId}", 
        "attemptNumber":${taskInfo.attemptNumber},
        "index":${taskInfo.index},
        "launchTime":${taskInfo.launchTime},
        "executorId":"${taskInfo.executorId}",
        "host":"${taskInfo.host}"
    }"""
}

val __pixiedustSparkListener = new SparkListener{
    private val channelReceiver = new ChannelReceiver()

    def setChannelListener(listener:PixiedustOutputListener){
		channelReceiver.setChannelListener(listener)
	}

    override def onJobStart(jobStart: SparkListenerJobStart) {
        channelReceiver.send("jobStart", s"""{
            "jobId":"${jobStart.jobId}",
            "stageInfos":${serializeStagesJSON(jobStart.stageInfos)}
        }
        """)
    }
    override def onJobEnd(jobEnd: SparkListenerJobEnd){
        val jobResult = jobEnd.jobResult match{
            case JobSucceeded => "Success"
            case _ => "Failure"
        }
        channelReceiver.send("jobEnd", s"""{
            "jobId":"${jobEnd.jobId}",
            "jobResult": "${jobResult}"
        }
        """)
    }

    override def onTaskStart(taskStart: SparkListenerTaskStart) { 
        channelReceiver.send("taskStart", s"""{
            "stageId":"${taskStart.stageId}",
            "taskInfo":${serializeTaskJSON(taskStart.taskInfo)}
        }
        """)
    }

    override def onTaskEnd(taskEnd: SparkListenerTaskEnd) { 
        channelReceiver.send("taskEnd", s"""{
            "stageId":"${taskEnd.stageId}",
            "taskType":"${taskEnd.taskType}",
            "taskInfo":${serializeTaskJSON(taskEnd.taskInfo)}
        }
        """)
    }

    override def onStageSubmitted(stageSubmitted: SparkListenerStageSubmitted) { 
        channelReceiver.send("stageSubmitted", s"""{
            "stageInfo": ${serializeStageJSON(stageSubmitted.stageInfo)}
        }
        """)
    }

    override def onTaskGettingResult(taskGettingResult: SparkListenerTaskGettingResult) { 
        //channelReceiver.send("taskGettingResult", s"taskGettingResult ${taskGettingResult.taskInfo.taskId} : ${taskGettingResult.taskInfo.executorId}")
    }

    override def onExecutorMetricsUpdate(executorMetricsUpdate: SparkListenerExecutorMetricsUpdate) { 
        //System.out.println(s"MetricsUpdate ${executorMetricsUpdate.execId} : ${executorMetricsUpdate.taskMetrics}")
    }

    override def onStageCompleted(stageCompleted: SparkListenerStageCompleted) { 
        channelReceiver.send("stageCompleted", s"""{
            "stageInfo":${serializeStageJSON(stageCompleted.stageInfo)}
        }
        """)
    }
}

sc.addSparkListener(__pixiedustSparkListener)
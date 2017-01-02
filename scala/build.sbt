name := "pixiedust"

version := "0.70"

scalaVersion := "2.11.8"

crossScalaVersions := Seq("2.10.4", "2.11.8") 

libraryDependencies ++= {
  val sparkVersion =  if (scalaVersion.value == "2.11.8") "2.0.2" else "1.6.0"
  Seq(
    "org.apache.spark" %%  "spark-core"	  %  sparkVersion % "provided",
    "org.apache.spark" %%  "spark-sql"  %  sparkVersion % "provided"
  )
}

assemblyMergeStrategy in assembly := {
  case PathList("org", "apache", "spark", xs @ _*) => MergeStrategy.first
  case PathList("scala", xs @ _*) => MergeStrategy.discard
  case PathList("META-INF", "maven", "org.slf4j", xs @ _* ) => MergeStrategy.first
  case x =>
    val oldStrategy = (assemblyMergeStrategy in assembly).value
    oldStrategy(x)
}

unmanagedBase <<= baseDirectory { base => base / "lib" }

assemblyOption in assembly := (assemblyOption in assembly).value.copy(includeScala = false)

resolvers += "scalaz-bintray" at "https://dl.bintray.com/scalaz/releases"
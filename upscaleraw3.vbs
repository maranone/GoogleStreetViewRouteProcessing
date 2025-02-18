test=0
howmanytimes=2
continue = false

Set objShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
inputVideo = "raw3.mp4"
outputFolder = ".\tempoutput"


if continue = true then
else





If Not FSO.FolderExists(outputFolder) Then
    Set objFolder = FSO.CreateFolder(outputFolder)
End If
Set objInputFolder = FSO.GetFolder(outputFolder)
For Each objFile In objInputFolder.Files
    If LCase(FSO.GetExtensionName(objFile.Path)) = "png" Then
        FSO.DeleteFile objFile.Path
    End If
Next

ffmpegCommand = "ffmpeg -i """ & inputVideo & """ -q:v 1 """ & outputFolder & "\image_%06d.png"""
objShell.Run ffmpegCommand, 0, True

inputFolder = ".\tempoutput"
outputFolder = ".\outputraw3"

Set objInputFolder = FSO.GetFolder(outputFolder)
For Each objFile In objInputFolder.Files
    If LCase(FSO.GetExtensionName(objFile.Path)) = "png" Then
        FSO.DeleteFile objFile.Path
    End If
Next

If Not FSO.FolderExists(outputFolder) Then
    Set objFolder = FSO.CreateFolder(outputFolder)
End If





end if
vulkanExe = "H:\realsr-ncnn-vulkan\realsr-ncnn-vulkan.exe"
inputFolder = ".\tempoutput"
outputFolder = ".\outputraw3"



Set objInputFolder = FSO.GetFolder(inputFolder)
totalFiles = objInputFolder.Files.Count
startTime = Timer()

numbertoskip = 0
okay = false
if continue = false then okay = true

For Each objFile In objInputFolder.Files
    howmany = howmany + 1
    if continue = true then
	if howmany > numbertoskip then okay = true
    end if

    if okay = true then


    currentPercentage = (howmany / totalFiles) * 100
    elapsedTime = Timer() - startTime
    estimatedTimeLeft = (elapsedTime / (howmany-numbertoskip)) * (totalFiles - (howmany-numbertoskip))

    wscript.echo "Processing File " & howmany & " of " & totalFiles & " - " & Round(currentPercentage, 2) & "%"
    wscript.echo "Elapsed Time: " & FormatTime(elapsedTime)
    wscript.echo "Estimated Time Left: " & FormatTime(estimatedTimeLeft)

    If howmany > howmanytimes And test = 1 Then
    Else
        vulkanCommand = """" & vulkanExe & """ -i """ & objFile.Path & """ -o .\output\" & objFile.Name & " -s 4 -f webp"
        If howmany Mod 2 = 0 Then
          wscript.echo vulkancommand
	  objShell.Run vulkanCommand, 0, True
        else
          wscript.echo vulkancommand
	  objShell.Run vulkanCommand, 0, false
          WScript.Sleep 2000
        end if
    End If


    end if
Next

Function FormatTime(seconds)
    hours = Int(seconds / 3600)
    minutes = Int((seconds Mod 3600) / 60)
    seconds = seconds Mod 60
    FormatTime = Right("0" & hours, 2) & ":" & Right("0" & minutes, 2) & ":" & Right("0" & seconds, 2)
End Function

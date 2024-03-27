''' internal used pulse secure connect script
Option Explicit

DIM oShell, fso, filePath, flag, configFile, line, con, kv
DIM pd, i, ei, fstr, comm, WaitOnReturn, cl, cc

SET oShell = WScript.CreateObject("WScript.Shell")
SET con = CreateObject("Scripting.Dictionary")

Function getConfig(BYVAL filePath, BYVAL mark)
    SET fso = CreateObject("Scripting.FileSystemObject")
    IF fso.FileExists(filePath) Then
        flag = 0
        SET configFile = fso.opentextfile(filePath, 1, TRUE)
        Do Until configFile.AtEndOfStream
            line = Trim(configFile.ReadLine())
            IF (flag = 1) Then
                IF InStr(line, "#") > 0 Then
                    i = 0
                ElseIF InStr(line, "=") > 0 Then
                    kv = Split(line, "=")
                    IF 1 = UBound(kv) Then
                        IF con.Exists(kv(0)) then
                            con.Remove(kv(0))
                        END IF
                        con.Add Trim(kv(0)), Trim(kv(1))
                    END IF
                ElseIF (InStr(line,"[") > 0 And InStr(line,"]") > 0) Then
                    Exit Do
                END IF
            END IF
            IF (LCase(line) = "[" & Lcase(mark) & "]") Then
                flag = 1
            END IF
        Loop
        configFile.Close
        SET fso = Nothing
    Else
        MsgBox("config file " & filePath & " does not exist plz check.")
    END IF
END Function

Function connect(BYVAL comm, BYVAL WaitOnReturn)
    connect = FALSE
    DIM rs:rs = oShell.run(comm, 0, WaitOnReturn)
    IF WaitOnReturn then
        IF rs = 0 Then
            connect = TRUE
        END IF
    END IF
END Function

''' verify if GP is connected ie ericsson internal network
Function testConnect(BYVAL comm)
    testConnect = FALSE
    FOR i = 1 To 10
        IF connect(comm, TRUE) THEN
            testConnect = TRUE
            EXIT FOR
        END IF
        wscript.Sleep(5000)
    NEXT
END Function

Function preConnect(BYVAL WaitOnReturn)
    IF con.Exists("u") and con.Exists("p") and con.Exists("url") THEN
        pd="""C:/Program Files (x86)/Common Files/Pulse Secure/Integration/pulselauncher.exe"" -u " & con.Item("u") & " -p " & con.Item("p") & " -r " & con.Item("r") & " -url " & con.Item("url")
        Call connect(pd, WaitOnReturn)
    END IF
END Function

filePath="./conn.ini"
Call getConfig(filePath, "pass")

ei="https://internal.ericsson.com/"
fstr="ericsson"
DIM sc:sc = "%comspec% /c curl -Iks " & ei & " | findstr /i " & fstr

IF testConnect(sc) THEN
    IF con.Exists("c") Then
        cl = Split(con.Item("c")," ")
        cc = ubound(cl)
        FOR Each i In cl
            WaitOnReturn = FALSE
            IF cc > 0 THEN
                cc = cc - 1
                WaitOnReturn = TRUE
            END IF
            Call getConfig(filePath, i)
            preConnect(WaitOnReturn)
        NEXT
    END IF
END IF

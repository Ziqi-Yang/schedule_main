from pandas import read_excel
import pandas as pd
from datetime import datetime
import re
import scheduleTime




class Schedule:
    def __init__(self,excel_path):
        self.excelPath = excel_path
        self.schedule = read_excel(excel_path,engine="openpyxl")
        self.initialize()

    def initialize(self):
        self.checkSchTime()
        self.testSch()



    def checkSchTime(self):
        """ check the schedule sheet for compliance"""
        time_intervals = scheduleTime.ScheduleTime(self.schedule.iloc[1:,0]).schedule
        self.schedule.insert(self.schedule.shape[1],"time_intervals",[None]+time_intervals)
    
    def addSchedule(self,i,dfLines,mode=1):
        df1 = self.todaySch.iloc[:i,:]
        if mode == 1: # replace
            df2 = self.todaySch.iloc[i+1:,:]
        elif mode == -1: # insert
            df2 = self.todaySch.iloc[i:,:]
        else:
            raise Exception("addSchdule Function doesn't support mode {}".format(mode))
        self.todaySch = pd.concat([df1,dfLines,df2],ignore_index=True)



    def getTodaySch(self,weekday):
        weekdayMap = {0:"星期一",1:"星期二",2:"星期三",3:"星期四",4:"星期五",5:"星期六",6:"星期日"}
        self.weekday = weekdayMap[weekday]
        # self.weekday = "星期六"
        self.todaySch = self.schedule[["time_intervals",self.weekday]]
        self.todayNotice = self.schedule.iloc[0,weekday+1]
        self.todaySch = self.todaySch.drop([0]) # drop notice, don't use inplace parameter because of some rules
    
    def parseCells(self):
        """
        supported label: "multi","section"
            "multi": a single cell contains multi tasks
            "section": combine the current cell with next cell(lower cell should be blank or has "section" label only)
        anything in the brackets will be ignored when parsing, but them will be in the body message(i.e. they will be sent)
        """
        schduleIndex = 0 # for addSchdule function
        for index in range(self.todaySch.shape[0]):
            cellIndex = index + 1 # pd.index label
            cell = self.todaySch[self.weekday][cellIndex]
            cellLines = cell.strip().split("\n")
            cellMode = cellLines[0][1:-1] if cellLines[0].strip() in ["[multi]","[section]"] else None
            if cellMode == None:
                pass
            elif cellMode == "multi":
                addScheduleMode = 1
                for line in cellLines:
                    line = line.strip()
                    if line[0] == "[" and line[-1] == "]":
                        continue
                    elif re.match(r"\d{2}[.:]\d{2}",line[:5]) != None:
                        if re.match(r"(\d{2}[.:]\d{2})-(\d{2}[.:]\d{2})",line[:11]) == None:
                            raise Exception("the format of the cell contains an error:\n{}".format(cell))

                        timeInterval = scheduleTime.TimeInterval(line[:11]).time_interval
                        newSchduleContent = line[11:].strip()
                        newSchdule = pd.DataFrame([[timeInterval,newSchduleContent]],columns=["time_intervals",self.weekday])
                        self.addSchedule(schduleIndex,newSchdule,mode=addScheduleMode)
                        addScheduleMode = -1 if addScheduleMode == 1 else -1 # only change once
                        schduleIndex += 1

            elif cellMode == "section":
                schedule = ""
                if index == self.todaySch.shape[0] - 1:
                    raise Exception("the [section] label couldn't be replaced in the last schdule")
                for line in cellLines:
                    line = line.strip()
                    if line[0] == "[" and line[-1] == "]":
                        continue
                    else:
                        schedule += line + "\n"
                if len(schedule) != 0:
                    schedule = schedule[:-1] # delete "\n"
                self.todaySch[self.weekday][cellIndex] = schedule
                self.todaySch[self.weekday][cellIndex + 1] = "继续-" + schedule

            schduleIndex += 1
        scheduleTime.checkCorrect(list(self.todaySch["time_intervals"])) # check for time overlap

    def testSch(self):
        """
        simulate the real excution, and ouput the all days's modified schdule respectively into one file
        """
        print("[*] Start testing {}, which may takes some time.".format(self.excelPath))
        for i in range(7):
            self.getTodaySch(datetime.today().weekday())
            self.parseCells()
        # restore to today's situation
        self.getTodaySch(datetime.today().weekday())
        self.parseCells()
        print("[*] Test finished. All things are in the right format.")
    
    def querySch(self,timeStr):
        """
        timeStr format: '%H:%M' , for example '01:02'
        """
        pass


        
    
if __name__ == "__main__":
    sch = Schedule("example.xlsx")
    print(sch.todaySch)

    # sch.getTodaySch(weekday)
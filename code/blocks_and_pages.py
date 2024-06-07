import queue
from enum import Enum
import random
from time import sleep
from PyQt5.QtCore import QThread, QMutex

#设置全局互斥锁
mutex = QMutex()

#全局常量
TOTAL_BLOCK = 4
PAGE_SIZE = 10
TOTAL_COMMAND=320
TOTAL_PAGE = TOTAL_COMMAND//PAGE_SIZE

#标识命令状态
class STATUS(Enum):
    UNHANDLED=0
    HANDELING=1
    HANDLED=2

#标识运行方式
class PROCESSMETHOD(Enum):
    CONTINUE=0  #连续执行
    SINGLE_CONTINUE=1   #单步执行-运行
    SINGLE_STOP=2   #单步执行-停止

#指令类
class Command:
    def __init__(self,num):
        self.No=num #指令编号
        self.handled=STATUS.UNHANDLED   #指令状态

#换页信息
class SwapInfo:
    def __init__(self):
        self.count=0
        self.currentNo=-1
        self.status=0
        self.inpage=-1
        self.outpage=-1

    def setcmdNum(self,currentNo):
        self.count+=1
        self.currentNo=currentNo

    def setinfo(self,inpage,outpage):
        self.status=1
        self.inpage=inpage
        self.outpage=outpage

    def reset(self):
        self.status=0
        self.inpage=-1
        self.outpage=-1

#页面
class Page:
    def __init__(self, num):
        self.id = num
        self.blockNum = -1
        self.content = [Command(i+num*PAGE_SIZE) for i in range(PAGE_SIZE)]

#内存块
class Block:
    def __init__(self,num):
        self.id=num
        self.pageNum=-1
        self.occupied=0 #是否被占用
        self.unaccessedTime = 0 #访问时间

#内存管理，继承自QThread，确保只能同时运行一条指令
class memManager(QThread):
    def __init__(self,method):
        super().__init__()
        self.pages=[Page(i) for i in range(TOTAL_PAGE)] #所有页面，编号0-31
        self.blocks=[Block(i) for i in range(TOTAL_BLOCK)]  #所有内存块，编号0-3
        self.accessList=queue.Queue(TOTAL_BLOCK)    #用于FIFO算法的访问队列
        self.method=method  #指定算法
        self.faultCount=0   #缺页数
        self.stopSign=False #停止标识
        self.pauseSign=False    #暂停标识
        self.processSign=PROCESSMETHOD.CONTINUE #运行标识
        self.handledCnt=0   #已运行指令数
        self.swapinfo=SwapInfo()    #换页信息

    #存储页面
    def store(self,blocknum,pagenum):   
        self.blocks[blocknum].pageNum=pagenum
        self.blocks[blocknum].occupied=1
        self.pages[pagenum].blockNum=blocknum

    #删除页面
    def delete(self,blocknum):
        if(self.blocks[blocknum].occupied):
            page_index = self.blocks[blocknum].pageNum
            if page_index != -1: 
                self.pages[page_index].blockNum = -1 
            self.blocks[blocknum].pageNum=-1
            self.blocks[blocknum].occupied=0
    
    #FIFO换页
    def doFIFO(self,pagenum):
        if(self.accessList.full()):
            removenum=self.accessList.get()
            self.swapinfo.setinfo(pagenum,self.blocks[removenum].pageNum)
            self.delete(removenum)
            self.store(removenum,pagenum)

    #LRU换页
    def doLRU(self,pagenum):
        maxUnaccessedTime=0
        result=0
        for i in range(TOTAL_BLOCK):
            if self.blocks[i].unaccessedTime>maxUnaccessedTime:
                maxUnaccessedTime=self.blocks[i].unaccessedTime
                result=i
        self.swapinfo.setinfo(pagenum,self.blocks[result].pageNum)
        self.delete(result)
        self.store(result,pagenum)

    #重置
    def reset(self):
        self.processSign=PROCESSMETHOD.CONTINUE
        self.stopSign=True

    #运行一条指令
    def oneCommand(self,commandNo):
        mutex.lock()    #自锁，防止其他进程访问
        #更改运行标识
        if(self.processSign!=PROCESSMETHOD.CONTINUE):
            self.processSign=PROCESSMETHOD.SINGLE_STOP
        cur_blocknum=self.pages[commandNo//PAGE_SIZE].blockNum
        self.swapinfo.setcmdNum(commandNo)  #设置换页信息-当前指令
        if cur_blocknum == -1:  #需要换页
            self.faultCount+=1
            fullFlag=True   
            for i in range(TOTAL_BLOCK):
                if self.blocks[i].occupied ==0:
                    fullFlag=False
                    break
            if fullFlag:    #内存块满，需要换页
                if self.method =='FIFO':
                    self.doFIFO(commandNo//PAGE_SIZE)
                elif self.method =='LRU':
                    self.doLRU(commandNo//PAGE_SIZE)
            else:   #内存块未满，直接存储在最近的空内存块
                self.swapinfo.setinfo(commandNo//PAGE_SIZE,-1)
                for i in range(TOTAL_BLOCK):
                    if self.blocks[i].occupied ==0:
                        self.store(i,commandNo//PAGE_SIZE)
                        break
            cur_blocknum=self.pages[commandNo//PAGE_SIZE].blockNum
            if self.method=='FIFO':
                self.accessList.put(cur_blocknum)
        else:   #不需要换页，重置换页信息
            self.swapinfo.reset()
        self.blocks[cur_blocknum].unaccessedTime = 0    #更新访问时间
        #更新指令状态
        self.pages[self.blocks[cur_blocknum].pageNum].content[commandNo%PAGE_SIZE].handled=STATUS.HANDELING
        sleep(0.12) #延时
        self.pages[self.blocks[cur_blocknum].pageNum].content[commandNo%PAGE_SIZE].handled=STATUS.HANDLED
        #处理单步执行的运行方式
        if(self.processSign!=PROCESSMETHOD.CONTINUE):
            while(self.processSign==PROCESSMETHOD.SINGLE_STOP):
                sleep(0.1)
        mutex.unlock()

    #切换换页算法
    def change_method(self,method):
        self.method=method

    #向前端传输当前内存块状态
    def get_current_status(self):
        current_blocks = [None for _ in range(TOTAL_BLOCK)]
        for i in range(TOTAL_BLOCK):
            if self.blocks[i].occupied != 0:
                page = self.pages[self.blocks[i].pageNum]
                page_info = {
                    'id': page.id,
                    'blockNum': page.blockNum,
                    'content': [{'No': cmd.No, 'handled': cmd.handled.value} for cmd in page.content]
                }
                current_blocks[i] = page_info
        return current_blocks
    
    #计算统计结果并告知前端
    def cal_params(self):
        if self.handledCnt!=0:
            faultRate= self.faultCount/self.handledCnt
        else:
            faultRate=0
        return {'faultCount':self.faultCount,'faultRate':faultRate}
    
    #向前端传输换页信息
    def get_swap_info(self):
        return {
            'Count':self.swapinfo.count,
            'StepNo':self.swapinfo.currentNo,
            'status': self.swapinfo.status,
            'inpage': self.swapinfo.inpage,
            'outpage': self.swapinfo.outpage
        }

    #改变暂停标识
    def change_pause_status(self):
        if(self.pauseSign):
            self.pauseSign=False
        else:
            self.pauseSign=True

    #改变执行方式
    def change_process_method(self):
        self.processSign=PROCESSMETHOD.CONTINUE

    #改变单步执行时的运行状态
    def change_single_status(self):
        if self.processSign==PROCESSMETHOD.SINGLE_CONTINUE:
            self.processSign=PROCESSMETHOD.SINGLE_STOP
        elif self.processSign==PROCESSMETHOD.SINGLE_STOP or self.processSign==PROCESSMETHOD.CONTINUE:
            self.processSign=PROCESSMETHOD.SINGLE_CONTINUE

    #完整进程管理，按照前地址-顺序执行-后地址-顺序执行的过程
    def startProcessing(self):
        currentNo=random.randint(0,319)
        self.oneCommand(currentNo)
        for cmdCount in range(TOTAL_COMMAND-1):
            if(self.stopSign):
                break
            while(self.pauseSign):  #等待继续运行的指令
                sleep(0.1)
            for i in range(TOTAL_BLOCK):
                self.blocks[i].unaccessedTime+=1
            if(currentNo>0 and cmdCount %4 == 0):   #前地址
                currentNo=random.randint(0,currentNo-1)
            if(currentNo<319 and cmdCount %4 == 1): #顺序执行
                currentNo+=1
            if(currentNo<318 and cmdCount %4 == 2): #后地址
                currentNo=random.randint(currentNo+1,319)
            if(currentNo<319 and cmdCount %4 == 3): #顺序执行
                currentNo+=1
            self.oneCommand(currentNo)
            self.handledCnt+=1
        self.stopSign=True
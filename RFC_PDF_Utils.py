#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
import io
import re
import sys
from PyPDF2 import PdfFileReader as reader,PdfFileWriter as writer
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import *
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfpage import PDFPage


pdfFilePath = r'./rfc.pdf'

class PDFHandleMode(object):
    # 保留源PDF文件的所有内容和信息，在此基础上修改
    COPY = 'copy'
    # 仅保留源PDF文件的页面内容，在此基础上修改
    NEWLY = 'newly'



class RFCPDFHandler(object):
    '''
    封装的PDF文件处理类
    '''
    def __init__(self, pdfFilePath, mode = PDFHandleMode.COPY):
        '''
        用一个PDF文件初始化

        :param pdfFilePath: PDF文件路径
        :param mode: 处理PDF文件的模式，默认为PDFHandleMode.COPY模式
        '''
        # 只读的PDF对象
        self.__pdf = reader(pdfFilePath)

        # 获取PDF文件名（不带路径）
        self.file_name = os.path.basename(pdfFilePath)
        #
        self.metadata = self.__pdf.getXmpMetadata()
        #
        self.doc_info = self.__pdf.getDocumentInfo()
        #
        self.pages_num = self.__pdf.getNumPages()

        # 可写的PDF对象，根据不同的模式进行初始化
        self.__writeable_pdf = writer()
        if mode == PDFHandleMode.COPY:
            self.__writeable_pdf.cloneDocumentFromReader(self.__pdf)
        elif mode == PDFHandleMode.NEWLY:
            for idx in range(self.pages_num):
                page = self.__pdf.getPage(idx)
                self.__writeable_pdf.insertPage(page, idx)


    def save2file(self,newFileName):
        '''
        将修改后的PDF保存成文件
        :param newFileName: 新文件名，不要和原文件名相同
        :return: None
        '''
        # 保存修改后的PDF文件内容到文件中
        with open(newFileName, 'wb') as fout:
            self.__writeable_pdf.write(fout)
        print('save2file success! new file is: {0}'.format(newFileName))


    def add_one_bookmark(self, title, page, parent = None, color = None, fit = '/Fit'):
        '''
        往PDF文件中添加单条书签，并且保存为一个新的PDF文件

        :param str title: 书签标题
        :param int page: 书签跳转到的页码，表示的是PDF中的绝对页码，值为1表示第一页
        :paran parent: A reference to a parent bookmark to create nested bookmarks.
        :param tuple color: Color of the bookmark as a red, green, blue tuple from 0.0 to 1.0
        :param list bookmarks: 是一个'(书签标题，页码)'二元组列表，举例：[(u'tag1',1),(u'tag2',5)]，页码为1代表第一页
        :param str fit: 跳转到书签页后的缩放方式
        :return: None
        '''
        # 为了防止乱码，这里对title进行utf-8编码
        self.__writeable_pdf.addBookmark(title.encode().decode('utf-8'),page - 1,parent = parent,color = color,fit = fit)
        print('add_one_bookmark success! bookmark title is: {0}'.format(title))


    def add_bookmarks_to_rfc_pdf(self, bookmarks):
        '''
        批量添加书签
        :param bookmarks: 书签元组列表，其中的页码表示的是PDF中的绝对页码，值为1表示第一页
        :return: None
        '''
        for title, page in bookmarks:
            self.add_one_bookmark(title, page)
        print('add_bookmarks_to_rfc_pdf success! add {0} pieces of bookmarks to PDF file'.format(len(bookmarks)))


    def read_bookmarks_from_txt(self,txt_file_path, page_offset = 0):
        '''
        从文本文件中读取书签列表
        文本文件有若干行，每行一个书签，内容格式为：
        书签标题 页码
        注：中间用空格隔开，页码为1表示第1页
        :param txt_file_path: 书签信息文本文件路径
        :param page_offset: 页码偏移量，为0或正数，即由于封面、目录等页面的存在，在PDF中实际的绝对页码比在目录中写的页码多出的差值
        :return: 书签列表
        '''
        bookmarks = []
        with open(txt_file_path,'r') as fin:
            for line in fin:
                line = line.rstrip()
                if not line:
                    continue
                # 以'@'作为标题、页码分隔符
                print('read line is: {0}'.format(line))
                try:
                    title = line.split('@')[0].rstrip()
                    page = line.split('@')[1].strip()
                except IndexError as msg:
                    print(msg)
                    continue
                # title和page都不为空才添加书签，否则不添加
                if title and page:
                    try:
                        page = int(page) + page_offset
                        print('page_offset is:', page_offset)
                        bookmarks.append((title, page))
                    except ValueError as msg:
                        print(msg)

        return bookmarks


    def get_rfc_pdf_catalogue(self, pdfFilePath, page_offset = 0):
        '''读取RFC文档中的目录，得到目录列表。'''
        fp = open(pdfFilePath, 'rb')  # 以二进制读模式打开文件
        # 用文件对象来创建一个pdf文档分析器
        parser = PDFParser(fp)
        # 创建一个PDF文档
        doc = PDFDocument(parser)
        # 连接分析器 与文档对象
        parser.set_document(doc)

        # 检测文档是否支持txt转换，不提供就忽略
        if not doc.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            # 创建PDf 资源管理器 来管理共享资源
            rsrcmgr = PDFResourceManager()
            # 创建一个PDF设备对象
            laparams = LAParams()
            device = PDFPageAggregator(rsrcmgr, laparams=laparams)
            # 创建一个PDF解释器对象
            interpreter = PDFPageInterpreter(rsrcmgr, device)

            bookmarks = []
            
            # 循环遍历列表，每次处理一个page的内容
            for page in PDFPage.create_pages(doc): # 生成page列表
                interpreter.process_page(page)
                # 接受该页面的LTPage对象
                layout = device.get_result()
                for x in layout:
                    if isinstance(x, LTTextBoxHorizontal):  # 获取文本内容
                        results = x.get_text()
                        refilter = re.compile(r"[.][.]\d")
                        replacefilter = re.compile(r"\.[.][.]*")
                        for line in results.splitlines():
                            if re.search(refilter, line):
                                line = re.sub(replacefilter, '@', line) + "\n"
                                try:
                                    title = line.split('@')[0].rstrip()
                                    page = line.split('@')[1].strip()
                                except IndexError as msg:
                                    print(msg)
                                    continue
                                # title和page都不为空才添加书签，否则不添加
                                if title and page:
                                    try:
                                        page = int(page) + page_offset
                                        # print('page_offset is:', page_offset)
                                        bookmarks.append((title, page))
                                    except ValueError as msg:
                                        print(msg)

            fp.close()

            return bookmarks

    def add_bookmarks_by_get_catalog_from_pdf(self, pdfFilePath, page_offset = 0):
        '''
        通过读取RFC pdf目录列表信息，将书签批量添加到PDF文件中

        :param txt_file_path: 书签列表信息文本文件
        :param page_offset: 页码偏移量，为0或正数，即由于封面、目录等页面的存在，在PDF中实际的绝对页码比在目录中写的页码多出的差值
        :return: None
        '''
        bookmarks = self.get_rfc_pdf_catalogue(pdfFilePath, page_offset)
        self.add_bookmarks_to_rfc_pdf(bookmarks)
        print('add_bookmarks_by_get_catalog_from_pdf success!')

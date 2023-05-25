import requests
from bs4 import BeautifulSoup
import re

year = ["2022", "2021", "2020"]
conference = ["acl", "aacl", "emnlp", "naacl"]
track_list = ["long", "main", "short", "findings"]
path = "/content/drive/MyDrive/Anthology_ResearchPaper/"
saved_file = "ResearchPaper.xlsx"
events = "https://aclanthology.org/events/"
key_words = ["effient", "vqa", "question answer", "machine translation", "bert", "time", "model", "large language model", "augmentation"]
count = {}

def get_html(event="https://aclanthology.org/events/", conference="acl", year="2022"):
  links =  event + conference + "-"+year
  html_doc = requests.get(links)
  paragraph = BeautifulSoup(html_doc.text, 'html.parser')
  return paragraph

def get_field(abstract, key_words):
  field = ""
  abstract = abstract.lower()

  for key in key_words:
    if key in abstract:
      if key not in count:
        count.update({key: 0})
      else:
        count[key] += 1
      field += key + ", "
  if field == '':
    field += "UNK,"
    if "Unk" not in count:
      count.update({"Unk": 0})
    else:
      count["Unk"] += 1

  field = field.strip()
  field= field[:-1]
  return field.upper()

def get_abstract(paragraph, year, conference, track, full_papers):
  # Get abstract
  abstract_tag = paragraph.find_all("div", {"class": "card bg-light mb-2 mb-lg-3 collapse abstract-collapse"})
  errors = []
  try:
    for abstract in abstract_tag:
      id = abstract["id"]
      abstract = abstract.find("div", {"class": "card-body p-3 small"}).text
      if track in id:
        id_number = re.findall("--\d+", id)
        if id_number:
          id_number = id_number[0].replace("--", "")
        else:
          return full_papers
        if int(id_number) == 0: 
          continue
        id = year+"."+conference+"-"+track+"."+id_number
        full_papers[track][id]["abstract"] = abstract
        full_papers[track][id]["fields"] = get_field(abstract, key_words)
        errors.append(id)
  except ValueError as e:
    print(e)
  return full_papers

def get_info(paragraph, year, conference, track, full_papers):
  para = paragraph.find_all("p", {"class": "d-sm-flex align-items-stretch"})
  for content in para:
    # text = content.text
    title = content.find_all("a", {"class": "align-middle"})
    authors = ""
    links = content.find_all('a', href=True)
    for link in links:
      if '.pdf' in link["href"]:
        li = link["href"].strip()
      elif 'people' in link["href"]:
        authors += link.text.strip() + ", "
      
    if track in li:
      id_number = re.findall("\.\d+.", li)
      if id_number:
        # print(id_number)
        id_number = id_number[0].replace(".", "")
      else:
        return full_papers
      # print(li)
      # print(id_number)
      if int(id_number) == 0: 
        continue
      id = year+"."+conference+"-"+track+"."+id_number
      paper_id = {"title": title[-1].text, "abstract": None, "link": li[:-4], "authors": authors.strip()[:-1], "fields": None}
      # print(id[:-4], " ", li[:-4])
      full_papers[track].update({id: paper_id})
  return full_papers

def mining_html(paragraph, year, conference, track):
  full_papers = {key: {} for key in track_list}
  full_papers = get_info(paragraph, year, conference, track, full_papers)
  full_papers = get_abstract(paragraph, year, conference, track, full_papers)
  return full_papers

import xlsxwriter

def write2xlsx(workbook, full_papers, worksheet=""):
  # worksheet = workbook.get_worksheet_by_name(worksheet)
  # if worksheet is None:
  #   worksheet = workbook.add_worksheet(worksheet)
  worksheet = workbook.add_worksheet(worksheet)
  cell_format = workbook.add_format({'text_wrap': True})
  # cell_format.set_pattern(1)  # This is optional when using a solid fill.
  cell_format.set_bg_color('yellow')
  cell_format.set_border(1)
  cell_format.set_center_across()
  # Add title
  title = {'A1': 'STT', 'B1': 'Id', 'C1': 'Title', 'D1': 'Abstract', 'E1': 'Link', 'F1': 'Authors', 'G1': 'Field'}
  column = ["C", 'D', 'E', 'F', 'G']
  worksheet.set_column(1, 2, 20)
  worksheet.set_column(2, 3, 30)
  worksheet.set_column(3, 4, 100)
  worksheet.set_column(4, 5, 30)
  worksheet.set_column(5, 6, 30)
  for ti in title:
    worksheet.write(ti, title[ti], cell_format)

  count = 1
  cell_format_abstract = workbook.add_format({'text_wrap': True})
  cell_format_abstract.set_align('align')
  cell_format_abstract.set_align('top')
  cell_format_abstract.set_border(1)
  for id in full_papers:
    count += 1
    cell_content_format = workbook.add_format({'text_wrap': True})
    cell_content_format.set_border(1)
    cell_content_format.set_align('top')
    cell_content_format.set_center_across()
    cell_content_format.set_border(1)
    worksheet.write('A'+str(count), count-1, cell_content_format)
    worksheet.write('B'+str(count), id, cell_content_format)
    for c, paper in zip(column, full_papers[id]):
      worksheet.write(c+str(count), full_papers[id][paper], cell_format_abstract)


if __name__=="__main__":
    workbook = xlsxwriter.Workbook(path+saved_file)

    for conf in conference:
        for y in year:
            print(conf + y)
            paragraph = get_html(events, conf, y)
            full_paper = {}
            for track in track_list:
                full_p = mining_html(paragraph, y, conf, track)
                full_paper.update(full_p[track])
                
                print(full_paper)
                if len(full_paper) != 0:
                    write2xlsx(workbook, full_paper, conf.upper()+y)

# workbook.close()
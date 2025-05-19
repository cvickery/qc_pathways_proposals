#! /usr/local/bin/python3
"""Generate an HTML archive of QC Pathways course approved prior to
"""

import phpserialize
import psycopg

from collections import defaultdict
from psycopg.rows import dict_row

# Current CUNYfirst course information
with psycopg.connect('dbname=cuny_curriculum') as conn:
  with conn.cursor(row_factory=dict_row) as cursor:
    cursor.execute("""
    select discipline||' '||catalog_number as course,
           title, course_status = 'A' as is_active,
           designation,
           attributes ~* 'WRIC' as is_wric,
           attributes ~* 'QNSLIT' as is_lit,
           attributes ~* 'QNSLANG' as is_lang,
           attributes ~* 'QNSSCI' as is_sci,
           attributes ~* 'QNSSYN' as is_syn
      from cuny_courses
     where institution ~* 'qns'
    """)
    rows = cursor.fetchall()

courses_cache = {row['course']: {'title': row['title'],
                                 'designation': row['designation'],
                                 'is_active': row['is_active'],
                                 'is_wric': row['is_wric'],
                                 'is_lit': row['is_lit'],
                                 'is_lang': row['is_lang'],
                                 'is_sci': row['is_sci'],
                                 'is_syn': row['is_syn']}
                 for row in rows}

conn = psycopg.connect('dbname=curric')
cursor = conn.cursor(row_factory=dict_row)

# Generate range of effective dates covered.
cursor.execute("""
select min("effective date"), max("effective date")
  from events_view
 where proposal > 160
   and ((agency = 'CCRC' and action = 'Approve')
        or (type in ('LIT', 'LANG', 'SCI', 'SYN') and agency = 'Senate' and action = 'Approve'))

""")
dates = cursor.fetchone()

earliest = dates['min'].strftime('%B, %Y')
latest = dates['max'].strftime('%B, %Y')

# Proposal categories and their criteria
required_core = ['EC-1', 'EC-2', 'MQR', 'LPS']
flexible_core = ['USED', 'WCGI', 'CE', 'IS', 'SW']
college_option = ['LIT', 'LANG', 'SCI', 'SYN']
cursor.execute("""
select abbr, full_name from proposal_types where abbr = ANY(%s)
""", (required_core + flexible_core + college_option, ))
proposal_types = {row['abbr']: row['full_name'] for row in cursor}

""" Get rid of “SLO-n:” at the beginning; handle embedded colons in the text.
"""
cursor.execute("""
select *
  from criteria
 where abbr !~* '^Admin|^Fix|^New|^Rev'
order by abbr""")
all_criteria = {row['abbr']: row['full_text'].split(':', maxsplit=1)[-1].strip().replace('  ', ' ')
                for row in cursor}

# All GenEd proposals have to satisfy criteria QC-1 and QC-2
qc_1 = all_criteria['QC-1']
qc_2 = all_criteria['QC-2']
# All Flexible Core proposals have to satisfy criteria FCC-1, FCC-2, and FCC-3
fcc_1 = all_criteria['FCC-1']
fcc_2 = all_criteria['FCC-2']
fcc_3 = all_criteria['FCC-3']
# Initial Lists of criteria
rc_criteria = {rd: {'QC-1': qc_1, 'QC-2': qc_2} for rd in required_core}
fc_criteria = {rd: {'QC-1': qc_1, 'QC-2': qc_2,
                    'FCC-1': fcc_1, 'FCC-2': fcc_2, 'FCC-3': fcc_3} for rd in flexible_core}
co_criteria = {rd: {'QC-1': qc_1, 'QC-2': qc_2} for rd in college_option}

# Complete the category lists
for abbr, full_text in all_criteria.items():
  match abbr:
    case s if s.startswith('EC'):
      rc_criteria['EC-1'][abbr] = full_text
    case s if s.startswith('CW-'):  # CW-n and CW2-n duplicate each other; skip CW2-n’s
      rc_criteria['EC-2'][abbr] = full_text
    case s if s.startswith('MQ'):
      rc_criteria['MQR'][abbr] = full_text
    case s if s.startswith('LP'):
      rc_criteria['LPS'][abbr] = full_text

    case s if s.startswith('WG'):
      fc_criteria['WCGI'][abbr] = full_text
    case s if s.startswith('US'):
      fc_criteria['USED'][abbr] = full_text
    case s if s.startswith('CE'):
      fc_criteria['CE'][abbr] = full_text
    case s if s.startswith('IS'):
      fc_criteria['IS'][abbr] = full_text
    case s if s.startswith('SW'):
      fc_criteria['SW'][abbr] = full_text

    case s if s.startswith('LI'):
      co_criteria['LIT'][abbr] = full_text
    case s if s.startswith('LA'):
      co_criteria['LANG'][abbr] = full_text
    case s if s.startswith('SC'):
      co_criteria['SCI'][abbr] = full_text
    case s if s.startswith('SY'):
      co_criteria['SYN'][abbr] = full_text

    case _:
      pass

# Table of Contents
toc = '<h2><a href="#criteria-prompts">Criteria Prompts</a></h2>'
# Required Core
toc += '<h2>Required Core Proposals</h2>\n'
for abbr in rc_criteria:
  toc += f'<div><a href="#{abbr}">{proposal_types[abbr]}</a></div>\n'
toc += '<h2>Flexible Core Proposals</h2>\n'
for abbr in fc_criteria:
  toc += f'<div><a href="#{abbr}">{proposal_types[abbr]}</a></div>\n'
toc += '<h2>College Option Proposals</h2>\n'
for abbr in co_criteria:
  toc += f'<div><a href="#{abbr}">{proposal_types[abbr]}</a></div>\n'

# Document Framework
print(f"""
<html>
  <head>
    <style>
      section {{
        break-before: page;
      }}
      .document-title {{
        text-align: center;
      }}
      #byline {{
        text-align: right;
        font-style: italic;
        font-size: 0.9em;
      }}
      #contents > div {{
        margin-left: 1em;
        border: 1px solid black;
        padding: 1em;
        border-radius: 0.25em;
      }}
      #prompts-intro {{
        font-size: 0.9em;
        font-style: italic;
        margin: 1em auto;
      }}
      #prompts-intro h1 {{
        font-style: normal;
      }}
      .inactive, .not-found {{
        color: red;
      }}
      /* PDF annotation support would require a paid-license version of PrinceXML. This is a model
       * of how that could be set up for a possible future extension of this project. Hovering over
       * a prompt‘s abbreviation could bring up a PDF annotation (tooltip) with the text of the
       * prompt instead of requiring the user to follow links back and forth between the prompt
       * definitions and the justificaion paragraphs.
      #required-core-annotation::after {{
        prince-pdf-annotate: text("Students must satisfy all four of these requirement areas")
      }}
      */
    </style>
  </head>
  <body>

    <h1 class="document-title">QC Approved Pathways Proposals</h1>
    <h2 class="document-title">{earliest} through {latest}</h2>

    <!-- Introduction -->
    <p>
      This is an archive of proposals for Pathways Common Core (Required Core and Flexible Core)
      courses that were approved by the Queens College Academic Senate and the CUNY Common Core
      Review Committee (CCRC). The Senate’s Undergraduate Curriculum Committee assigned the task of
      collecting and reviewing these proposals to the <em>ad hoc</em> General Education Advisory
      Committee (GEAC). The chair of GEAC, Christopher Vickery, developed a database and website
      for managing proposal submissions, peer review, and subsequent public record. The College has
      stopped hosting the website, but a copy of the underlying database has been preserved, and
      was used to generate this archive of the successful propoposals.
    </p>

    <p>
      CCRC proposals must be accompanied by a highly-structured sample syllabus for the course.
      Those syllabi are not included in this archive.
    </p>

    <p>
      College Option requirements are not subject to CCRC review, and need only be approved by the
      Academic Senate. Those proposals are included in this archive as well.
    </p>

    <p>
      For this archive, each course was examined in the <em>current</em> CUNYfirst course catalog.
      Courses that are currently missing or inactive are noted. Otherwise, each course’s current
      title is given, followed by a series of course properties in square brackets. Within the
      square brackets, the first property is the <em>designation</em>, which will normally match the
      proposal type. Following the designation, WI means the course is writing intensive, while LIT,
      LANG, SCI, and SYN indicate the four college option categories.
    </p>

    <p>
      <strong>Implementation Note:</strong> The archive used a preserved copy of the database to
      build a static web page using Python code. That code is
      <a href="https://github.com/cvickery/qc_pathways_proposals">publicly available on GitHub</a>.
      That web page was then converted to PDF using the <a href="https://princexml.com">Prince</a>
      conversion tool. (That’s the Prince logo in the upper right corner of this page). A dump of
      the Postgres database is available from the author.
    </p>

    <p id="byline">
      Christopher Vickery<br/>
      May, 2025
    </p>

    <section id="contents">
    <h2>Contents</h2>
    <div>{toc}</div>
    </section>

    <section id="prompts-intro">
    <h1 id="criteria-prompts">Criteria Prompts</h1>
      <p>
        These are the criteria (prompts) for the various Pathways categories. In the
        proposals that follow, only the abbreviations are shown.
      </p>
      <p>
        All QC GenEd proposals must address the two criteria, QC-1 and QC-2. but the justifications
        for these two criteria are not submitted to the CUNY Common Core Review Committee.
      </p>
      <p>
        Flexible Core proposals must address all three of criteria, FCC-1, FCC-2, and FCC-3, plus
        three of the additional criteria specific to each FCC area.
      </p>
      <p>
        College Option proposals are not submitted to the CUNY Common Core Review Committee. They
        require only Academic Senate approval.
      </p>
    </section>
""")
print('<h2 id="required-core-annotation">Required Core '
      'Criteria</h2>')
for key, criterion in rc_criteria.items():
  print(f'<h3 id="criteria-{key}">{key}: {proposal_types[key]}</h3>')
  for k, v in criterion.items():
    print(f'<p><strong>{k}</strong>: {v}</p>')
  print(f'<p><a href="#{key}">{key} Proposals</a>')

print('<h2>Flexible Core Criteria</h2>')
for key, criterion in fc_criteria.items():
  print(f'<h3 id="criteria-{key}">{key}: {proposal_types[key]}</h3>')
  for k, v in criterion.items():
    print(f'<p><strong>{k}</strong>: {v}</p>')
  print(f'<p><a href="#{key}">{key} Proposals</a>')

print('<h2>College Option Criteria</h2>')
for key, criterion in co_criteria.items():
  print(f'<h3 id="criteria-{key}">{key}: {proposal_types[key]}</h3>')
  for k, v in criterion.items():
    print(f'<p><strong>{k}</strong>: {v}</p>')
  print(f'<p><a href="#{key}">{key} Proposals</a>')


def php_object_to_dict(name, attrs):
  return attrs  # discard the PHP class name


by_type = defaultdict(dict)

# Common Core proposals approved by CCRC
query = """
select e.proposal, e.course, e.type, e."effective date" as effective_date, p.justifications
  from events_view e, proposals p
 where p.id = e.proposal
   and agency  ='CCRC'
   and action = 'Approve'
order by proposal;
"""
cursor.execute(query)
for row in cursor:
  row['type'] = 'SW' if row['type'] == 'REV-U' else row['type']  # GEOL 77 was both REV-U and SW
  # print(f'{row['proposal']} {row['type']:5} {row['course']:10} {row['effective_date']}')
  if row['type'] not in required_core + flexible_core + college_option:
    print(f'*** Unexpected proposal type: {row}')
  justifications = phpserialize.loads(row['justifications'].encode('utf-8'),
                                      decode_strings=True,
                                      object_hook=php_object_to_dict)
  by_type[row['type']][row['course']] = {'justifications': justifications,
                                         'effective_date': row['effective_date']}

# College Option proposals approved by the Senate
# Common Core courses approved by CCRC
query = """
select e.proposal, e.course, e.type, e."effective date" as effective_date, p.justifications
  from events_view e, proposals p
 where p.id = e.proposal
   and e.type in ('LIT', 'LANG', 'SCI', 'SYN')
   and agency  ='Senate'
   and action = 'Approve'
order by proposal;
"""
cursor.execute(query)
for row in cursor:
  if row['type'] not in required_core + flexible_core + college_option:
    print(f'*** Unexpected proposal type: {row}')
  justifications = phpserialize.loads(row['justifications'].encode('utf-8'),
                                      decode_strings=True,
                                      object_hook=php_object_to_dict)
  by_type[row['type']][row['course']] = {'justifications': justifications,
                                         'effective_date': row['effective_date']}

# Generate the proposals
for proposal_type in required_core + flexible_core + college_option:
  print(f'<h1 id="{proposal_type}" class="proposal-type">{proposal_types[proposal_type]} '
        f'Proposals</h1>')
  print(f'<p><a href="#criteria-{proposal_type}">{proposal_type} Criteria Definitions</a></p>')
  courses = sorted(by_type[proposal_type])
  if len(courses) < 1:
    print('<h3>No Approved Proposals</h3>')
  else:
    print('<div>' +
          ' ● '.join([f'<a href="#{proposal_type+course.replace(' ', '')}">{course}</a>'
                      for course in courses]) +
          '</div>')
    for course in courses:
      try:
        course_info = courses_cache[course.rstrip('WH')]
        if course_info['is_active']:
          designation = course_info['designation']
          if designation[0] in ['R', 'F'] and designation[-1] == 'R':
            designation = designation[1:3]
          info_str = f'{course_info['title']} [{designation}'
          info_str += ' WRIC' if course_info['is_wric'] else ''
          info_str += ' LIT' if course_info['is_lit'] else ''
          info_str += ' LANG' if course_info['is_lang'] else ''
          info_str += ' SCI' if course_info['is_sci'] else ''
          info_str += ' SYN' if course_info['is_syn'] else ''
          info_str += ']'
        else:
          info_str = '<span class="inactive">Currently Inactive</span>'
      except KeyError:
        info_str = '<span class="not-found">Not Found</span>'
      proposal = by_type[proposal_type][course]
      print(f'<h3 id="{proposal_type+course.replace(' ', '')}">{course} {info_str}</h3>'
            f'<h4>Approved {proposal['effective_date']}</h4>')
      for abbr, full_text in proposal['justifications'].items():
        print(f'<p><strong>{abbr}:</strong> {full_text}</p>')

print('</body></html>')

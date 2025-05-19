# Archive old Queens College Pathways proposals

Use a saved copy of the Postgres database underlying the proposal management system to generate an HTML representation of approved proposals.

Uses <a href="https://princexml.com">Prince 16</a> to convert the HTML to PDF.

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

from bisect import bisect_left
from collections import OrderedDict
from enum import Enum
from math import ceil
import argparse, re, sys
import dominate
from dominate import tags

class Format(Enum):
    console = 1
    html = 2
    markdown = 3

# This is an object instead of naive strings in Student because names are 
# complicated and in the long run it's only a matter of time until the
# simple version doesn't work.  This particular name is representative
# of the western Europe/American style of [Given Name] [Paternal Name]
class Name(object):
    def __init__(self, first, last):
        self.first = first
        self.last = last

class GradeTiers(object):
    def __init__(self, tiers):
        self._tiers = tiers
        self._sorted = False

    def sort_before_run(func):
        def inner(self, *args):
            if not self._sorted:
                tiers = list(self._tiers) # We need a copy since lists are
                                          # passed reference and someone else
                                          # might be depending on its order
                tiers.sort(key=lambda item: item[0]) # Sort by the value
                self._tiers = OrderedDict(tiers)
                self._sorted = True
            return func(self, *args)
        return inner

    @sort_before_run
    def letter(self, percentile_grade):
        return self._tiers[GradeTiers
                          .get_closest_percentage_key(percentile_grade, 
                                                      self._tiers.keys())]

    @staticmethod
    def get_closest_percentage_key(percentile_grade, percentage_keys):
        pos = bisect_left(percentage_keys, percentile_grade)
        if pos >= len(percentage_keys):
            return percentage_keys[-1]
        else:
            return percentage_keys[pos]

class GradeBook(object):
    def __init__(self, grade_tiers):
        self.students = set()
        self._grade_tiers = grade_tiers
        self.output_type_callbacks = {
            Format.console : self.get_student_grades_console,
            Format.html : self.get_student_grades_html,
            Format.markdown : self.get_student_grades_markdown
        }

    def add(self, student):
        self.students.add(student)

    def get_number_of_assignments(self):
        return max([len(student.scores) for student in self.students])

    def get_student_grades(self, output_type=Format.console):
        return self.output_type_callbacks[output_type]()

    def get_student_grades_console(self):
        # Need to run 'pip install texttable' before using this
        from texttable import Texttable
        table = Texttable()
        header = ['First Name', 'Last Name', 'Overall Average', 'Letter Grade']
        for i in xrange(1, self.get_number_of_assignments() + 1):
            header.append('Score {0}'.format(i))
        table.add_row(header)
        number_of_assignments = self.get_number_of_assignments()
        for student in self.sorted_students():
            grade_average = student.grade_average(number_of_assignments)
            row = [student.name.first,
                   student.name.last,
                   grade_average,
                   self._grade_tiers.letter(grade_average)]
            for score in student.scores:
                row.append(str(score))
            while len(row) < len(header):
                row.append(None)
            print row
            table.add_row(row)
        return table.draw()

    def get_student_grades_html(self):
        page = dominate.document(title='Final Grades')
        with page:
            with tags.table(border="1"):
                number_of_assignments = self.get_number_of_assignments()
                with tags.tr():
                    tags.th("First Name")
                    tags.th("Last Name")
                    tags.th("Overall Average")
                    tags.th("Letter Grade")
                    tags.th("Scores", colspan=str(number_of_assignments))
                for student in self.sorted_students():
                    with tags.tr():
                        grade_average = student.grade_average(number_of_assignments)
                        tags.td(student.name.first)
                        tags.td(student.name.last)
                        tags.td(grade_average)
                        tags.td(self._grade_tiers.letter(grade_average))
                        for score in student.scores:
                            tags.td(score)
        return str(page)

    def get_student_grades_markdown(self):
        number_of_assignments = self.get_number_of_assignments()
        to_return =  "First Name | Last Name | Overall Average | Letter Grade | {0} |\n"\
                     .format(' | '\
                             .join(['Score {0}'.format(i) for i in xrange(1, number_of_assignments + 1)]))
        to_return += "-----------|-----------|-----------------|--------------|{0}|\n"\
                     .format('|'\
                             .join(['------'.format(i) for i in xrange(0, number_of_assignments)]))
        for student in self.sorted_students():
            grade_average = student.grade_average(number_of_assignments)
            to_return += "{0} | {1} | {2} | {3} | {4} |\n"\
                            .format(student.name.first,
                                    student.name.last,
                                    grade_average,
                                    self._grade_tiers.letter(grade_average),
                                    ' | '.join([str(score) for score in student.scores]))
        return to_return

    def sorted_students(self):
        number_of_assignments = self.get_number_of_assignments()
        return sorted(self.students, 
                      key=lambda student:
                              student.grade_average(number_of_assignments), 
                      reverse=True)

    @staticmethod
    def parse(infile, grade_tiers):
        lines = infile.readlines()
        to_return = GradeBook(grade_tiers)
        for line in lines:
            to_return.add(GradeBook.parse_student(line))
        return to_return

    @staticmethod
    def parse_student(line):
        match = re.match(r'^(\S+)\s+(\s*\D+)+\s*(.*)', line)
        first_name, last_name = match.group(1), match.group(2).strip()
        scores = [float(x) for x in re.split(r'\s+', match.group(3).strip())]
        return Student(Name(first_name, last_name), scores)

class Student(object):
    def __init__(self, name, scores):
        self.name = name
        self.scores = scores

    def grade_average(self, number_of_assignments=None):
        if number_of_assignments is None:
            number_of_assignments = float(len(self.scores))
        # Specifically want to use floats to avoid integer rounding
        return ceil(sum(self.scores)/number_of_assignments)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calculate students' grades for a semester.")

    parser.add_argument('-i', '--input', action='store', default=None, dest='input', help='Input file to use.  If not provided, uses stdin.')
    parser.add_argument('-o', '--output', action='store', default=None, dest='output', help='Output file to use.  If not provided, uses stdin.')
    parser.add_argument('-f', '--format', action='store', default='console', dest='format', choices=[name.lower() for name, member in Format.__members__.items()])

    args = parser.parse_args()
    args.format = Format[args.format]

    # I considered getting cute and using division and ASCII math, but this 
    # way grade tiers can be set to whatever
    tiers = GradeTiers([(59, 'F'),
                        (62, 'D-'),
                        (65, 'D'),
                        (69, 'D+'),
                        (72, 'C-'),
                        (75, 'C'),
                        (79, 'C+'),
                        (82, 'B-'),
                        (85, 'B'),
                        (89, 'B+'),
                        (92, 'A-'),
                        (100, 'A')])

    with (open(args.input) if args.input is not None else sys.stdin) as infile:
        with (open(args.output, 'w') if args.output is not None else sys.stdout) as outfile:
            grade_book = GradeBook.parse(infile, tiers)
            print grade_book.get_student_grades(args.format)

import re

from django.db import models
from users.models import NewUser
from django.utils import timezone



class Project(models.Model):
    owner       = models.ForeignKey(NewUser, on_delete=models.CASCADE, related_name="projects")
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    @property
    def word_count(self):
        total = 0
        for chapter in self.chapters.all():
            for section in chapter.sections.all():
                if section.content:
                    total += len(section.content.split())
        return total


    @property
    def page_count(self):
        return max(1, round(self.word_count / 250)) if self.word_count else 0


    @property
    def reference_count(self):
        """
        Count unique references across all section content.
        Detects:
          - APA in-text:  (Smith, 2020)  /  (Smith & Jones, 2020)
          - Numbered:     [1], [2], [14]
          - Footnote:     ¹  ²  ³  (superscript digits)
        """
        all_content = ''
        for chapter in self.chapters.all():
            for section in chapter.sections.all():
                if section.content:
                    all_content += section.content + '\n'

        if not all_content:
            return 0

        # APA style: (Author, Year) or (Author & Author, Year)
        apa = set(re.findall(
            r'\([A-Z][a-zA-Z\-]+(?:\s*(?:&|et al\.)\s*[A-Z][a-zA-Z\-]+)?,\s*\d{4}\)',
            all_content
        ))

        # Numbered style: [1], [2], etc — collect unique numbers
        numbered = set(re.findall(r'\[(\d+)\]', all_content))

        # Combine: if numbered refs found, use their count; else use APA count
        if numbered:
            return len(numbered)
        return len(apa)


    @property
    def completion_pct(self):
        total = 0
        filled = 0

        for chapter in self.chapters.all():
            for section in chapter.sections.all():
                total += 1
                if section.content and section.content.strip():
                    filled += 1

        return round((filled / total) * 100) if total else 0


CHAPTER_ICONS = {
    1: "📘",
    2: "📕",
    3: "📗",
    4: "📙",
    5: "📓",
}

DEFAULT_CHAPTERS = [
    (1, "Introduction",                    ""),
    (2, "Literature Review",               "Literature Review"),
    (3, "Methodology",                     "Methodology"),
    (4, "Data Analysis",                   "Data Analysis"),
    (5, "Summary, Conclusion & Recommendation", "Summary, Conclusion & Recommendation"),
]

DEFAULT_SECTIONS = {
    1: ["Background of Study", "Problem Statement", "Aim & Objectives",
        "Research Questions", "Scope of Study"],
    2: ["Conceptual Framework", "Theoretical Framework", "Empirical Review",
        "Gap in Literature"],
    3: ["Research Design", "Population & Sample", "Data Collection Instruments",
        "Validity & Reliability", "Data Analysis Technique"],
    4: ["Data Presentation", "Discussion of Findings", "Hypothesis Testing"],
    5: ["Summary", "Conclusion", "Recommendations", "Limitations",
        "Suggestions for Further Study"],
}

class Reference(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="references"
    )
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=10, blank=True)
    source = models.TextField(blank=True)

    def __str__(self):
        return self.title
    

class Chapter(models.Model):
    project  = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="chapters")
    number   = models.PositiveSmallIntegerField()
    title    = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    is_open  = models.BooleanField(default=False)

    class Meta:
        ordering = ["number"]
        unique_together = ("project", "number")

    def __str__(self):
        return f"Chapter {self.number}: {self.title}"

    @property
    def icon(self):
        return CHAPTER_ICONS.get(self.number, "📄")
    
    @property
    def word_count(self):
        total = 0
        for section in self.sections.all():
            if section.content:
                total += len(section.content.split())
        return total

    @property
    def page_count(self):
        return round(self.word_count / 250) or 0


class Section(models.Model):
    chapter    = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="sections")
    title      = models.CharField(max_length=255)
    order      = models.PositiveSmallIntegerField(default=0)
    content    = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.number} {self.title}"

    @property
    def number(self):
        return f"{self.chapter.number}.{self.order}"

    @property
    def word_count(self):
        return len(self.content.split()) if self.content else 0

    @property
    def page_count(self):
        return round(self.word_count / 250) or 0


class ChatMessage(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]

    section   = models.ForeignKey(Section, on_delete=models.CASCADE,
                                  related_name="chat_messages")
    role      = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content   = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:60]}"
    
    @property
    def word_count(self):
        total = 0
        for chapter in self.chapters.all():
            for section in chapter.sections.all():
                if section.content:
                    total += len(section.content.split())
        return total

    @property
    def page_count(self):
        return round(self.word_count / 250) or 0

    @property
    def completion_pct(self):
        total = 0
        filled = 0

        for chapter in self.chapters.all():
            for section in chapter.sections.all():
                total += 1
                if section.content and section.content.strip():
                    filled += 1

        return round((filled / total) * 100) if total else 0

from cloudinary.models import CloudinaryField

class Dataset(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="datasets"
    )
    # CloudinaryField for file uploads (supports all file types)
    file = CloudinaryField(
        'dataset_file',
        folder='datasets/',           # optional: subfolder in Cloudinary
        resource_type='auto',         # auto-detect file type (csv, xlsx, etc.)
        overwrite=True,               # overwrite existing with same public_id
        format=None,                  # keep original format
        blank=True,
        null=True
    )
    name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name or (self.file.public_id if self.file else 'Unnamed')
    
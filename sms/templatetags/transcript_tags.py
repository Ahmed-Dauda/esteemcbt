from django import template

register = template.Library()

@register.filter
def split_transcript(transcript):
    return transcript.split("\n")

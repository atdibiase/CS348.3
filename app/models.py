from django.db import models

class Team(models.Model):
    season = models.CharField(max_length=20)
    name = models.CharField(max_length=80)
    coach = models.CharField(max_length=80, default="Unknown")
    city = models.CharField(max_length=80)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    win_percentage = models.FloatField(default=0.0)

    def __str__(self):
        return f'{self.name} ({self.season})'

class Game(models.Model):
    date = models.DateField()
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_games')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_games')
    location = models.CharField(max_length=120)
    home_score = models.PositiveIntegerField()
    away_score = models.PositiveIntegerField()

    @property
    def winner(self):
        if self.home_score > self.away_score:
            return self.home_team.name
        elif self.home_score < self.away_score:
            return self.away_team.name
        
    def save(self, *args, **kwargs):
        if self.home_team:
            self.location = self.home_team.city
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"
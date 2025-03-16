class LessonPlan {
  final String title;
  final String description;
  final String knowledgeLevel;
  final int durationMinutes;
  final List<String> learningObjectives;
  final List<LessonActivity> activities;
  final LessonAssessment assessment;
  final List<String> nextSteps;
  final String generatedAt;
  final String userId;
  final String topic;

  LessonPlan({
    required this.title,
    required this.description,
    required this.knowledgeLevel,
    required this.durationMinutes,
    required this.learningObjectives,
    required this.activities,
    required this.assessment,
    required this.nextSteps,
    required this.generatedAt,
    required this.userId,
    required this.topic,
  });

  factory LessonPlan.fromJson(Map<String, dynamic> json) {
    return LessonPlan(
      title: json['title'] as String,
      description: json['description'] as String,
      knowledgeLevel: json['knowledge_level'] as String,
      durationMinutes: json['duration_minutes'] as int,
      learningObjectives: (json['learning_objectives'] as List)
          .map((e) => e as String)
          .toList(),
      activities: (json['activities'] as List)
          .map((e) => LessonActivity.fromJson(e as Map<String, dynamic>))
          .toList(),
      assessment:
          LessonAssessment.fromJson(json['assessment'] as Map<String, dynamic>),
      nextSteps: (json['next_steps'] as List).map((e) => e as String).toList(),
      generatedAt: json['generated_at'] as String,
      userId: json['user_id'] as String,
      topic: json['topic'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'description': description,
      'knowledge_level': knowledgeLevel,
      'duration_minutes': durationMinutes,
      'learning_objectives': learningObjectives,
      'activities': activities.map((e) => e.toJson()).toList(),
      'assessment': assessment.toJson(),
      'next_steps': nextSteps,
      'generated_at': generatedAt,
      'user_id': userId,
      'topic': topic,
    };
  }
}

class LessonActivity {
  final String title;
  final String type;
  final int durationMinutes;
  final String description;
  final List<LessonResource> resources;

  LessonActivity({
    required this.title,
    required this.type,
    required this.durationMinutes,
    required this.description,
    required this.resources,
  });

  factory LessonActivity.fromJson(Map<String, dynamic> json) {
    return LessonActivity(
      title: json['title'] as String,
      type: json['type'] as String,
      durationMinutes: json['duration_minutes'] as int,
      description: json['description'] as String,
      resources: (json['resources'] as List)
          .map((e) => LessonResource.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'type': type,
      'duration_minutes': durationMinutes,
      'description': description,
      'resources': resources.map((e) => e.toJson()).toList(),
    };
  }
}

class LessonResource {
  final String title;
  final String type;
  final String description;

  LessonResource({
    required this.title,
    required this.type,
    required this.description,
  });

  factory LessonResource.fromJson(Map<String, dynamic> json) {
    return LessonResource(
      title: json['title'] as String,
      type: json['type'] as String,
      description: json['description'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'type': type,
      'description': description,
    };
  }
}

class LessonAssessment {
  final String type;
  final String description;
  final List<String> criteria;

  LessonAssessment({
    required this.type,
    required this.description,
    required this.criteria,
  });

  factory LessonAssessment.fromJson(Map<String, dynamic> json) {
    return LessonAssessment(
      type: json['type'] as String,
      description: json['description'] as String,
      criteria: (json['criteria'] as List).map((e) => e as String).toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'description': description,
      'criteria': criteria,
    };
  }
}

class Curriculum {
  final String title;
  final String description;
  final int totalDurationMinutes;
  final String userId;
  final String generatedAt;
  final List<CurriculumModule> modules;

  Curriculum({
    required this.title,
    required this.description,
    required this.totalDurationMinutes,
    required this.userId,
    required this.generatedAt,
    required this.modules,
  });

  factory Curriculum.fromJson(Map<String, dynamic> json) {
    return Curriculum(
      title: json['title'] as String,
      description: json['description'] as String,
      totalDurationMinutes: json['total_duration_minutes'] as int,
      userId: json['user_id'] as String,
      generatedAt: json['generated_at'] as String,
      modules: (json['modules'] as List)
          .map((e) => CurriculumModule.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'description': description,
      'total_duration_minutes': totalDurationMinutes,
      'user_id': userId,
      'generated_at': generatedAt,
      'modules': modules.map((e) => e.toJson()).toList(),
    };
  }
}

class CurriculumModule {
  final String topic;
  final double knowledgeLevel;
  final int durationMinutes;
  final LessonPlan lessonPlan;

  CurriculumModule({
    required this.topic,
    required this.knowledgeLevel,
    required this.durationMinutes,
    required this.lessonPlan,
  });

  factory CurriculumModule.fromJson(Map<String, dynamic> json) {
    return CurriculumModule(
      topic: json['topic'] as String,
      knowledgeLevel: (json['knowledge_level'] as num).toDouble(),
      durationMinutes: json['duration_minutes'] as int,
      lessonPlan:
          LessonPlan.fromJson(json['lesson_plan'] as Map<String, dynamic>),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'topic': topic,
      'knowledge_level': knowledgeLevel,
      'duration_minutes': durationMinutes,
      'lesson_plan': lessonPlan.toJson(),
    };
  }
}

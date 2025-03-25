class UserProgress {
  final String userId;
  final double averageKnowledge;
  final int topicsStudied;
  final List<TopicProgress> weakTopics;
  final List<TopicProgress> mediumTopics;
  final List<TopicProgress> strongTopics;

  UserProgress({
    required this.userId,
    required this.averageKnowledge,
    required this.topicsStudied,
    required this.weakTopics,
    required this.mediumTopics,
    required this.strongTopics,
  });

  factory UserProgress.fromJson(Map<String, dynamic> json) {
    // Handle the case when the API returns 'topics' instead of categorized topics
    if (json.containsKey('topics')) {
      // If we have a flat 'topics' list, categorize them here
      final List<TopicProgress> allTopics = [];

      if (json['topics'] is List) {
        allTopics.addAll((json['topics'] as List)
            .map((e) => e is Map<String, dynamic>
                ? TopicProgress.fromJson(e)
                : TopicProgress(
                    name: e.toString(),
                    level: 0,
                    lastUpdated: DateTime.now().toIso8601String(),
                  ))
            .toList());
      }

      // Categorize topics based on knowledge level
      final weakTopics = allTopics.where((t) => t.level < 40).toList();
      final mediumTopics =
          allTopics.where((t) => t.level >= 40 && t.level < 70).toList();
      final strongTopics = allTopics.where((t) => t.level >= 70).toList();

      return UserProgress(
        userId: json['user_id'] != null
            ? json['user_id'] as String
            : "default_user",
        averageKnowledge: (json['average_knowledge'] as num? ?? 0).toDouble(),
        topicsStudied: json['topics_studied'] as int? ?? 0,
        weakTopics: weakTopics,
        mediumTopics: mediumTopics,
        strongTopics: strongTopics,
      );
    }

    // Handle the standard case with categorized topics
    return UserProgress(
      userId:
          json['user_id'] != null ? json['user_id'] as String : "default_user",
      averageKnowledge: (json['average_knowledge'] as num? ?? 0).toDouble(),
      topicsStudied: json['topics_studied'] as int? ?? 0,
      weakTopics: json.containsKey('weak_topics') && json['weak_topics'] != null
          ? (json['weak_topics'] as List)
              .map((e) => TopicProgress.fromJson(e as Map<String, dynamic>))
              .toList()
          : [],
      mediumTopics:
          json.containsKey('medium_topics') && json['medium_topics'] != null
              ? (json['medium_topics'] as List)
                  .map((e) => TopicProgress.fromJson(e as Map<String, dynamic>))
                  .toList()
              : [],
      strongTopics:
          json.containsKey('strong_topics') && json['strong_topics'] != null
              ? (json['strong_topics'] as List)
                  .map((e) => TopicProgress.fromJson(e as Map<String, dynamic>))
                  .toList()
              : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'average_knowledge': averageKnowledge,
      'topics_studied': topicsStudied,
      'weak_topics': weakTopics.map((e) => e.toJson()).toList(),
      'medium_topics': mediumTopics.map((e) => e.toJson()).toList(),
      'strong_topics': strongTopics.map((e) => e.toJson()).toList(),
    };
  }
}

class TopicProgress {
  final String name;
  final double level;
  final String lastUpdated;
  final String status;
  final int studySessions;
  final int quizAttempts;
  final int flashcardSessions;
  final int totalStudyMinutes;

  TopicProgress({
    required this.name,
    required this.level,
    required this.lastUpdated,
    this.status = '',
    this.studySessions = 0,
    this.quizAttempts = 0,
    this.flashcardSessions = 0,
    this.totalStudyMinutes = 0,
  });

  factory TopicProgress.fromJson(Map<String, dynamic> json) {
    return TopicProgress(
      name: json['name'] as String,
      level: (json['level'] as num).toDouble(),
      lastUpdated: json['last_updated'] as String,
      status: json['status'] as String? ?? '',
      studySessions: json['study_sessions'] as int? ?? 0,
      quizAttempts: json['quiz_attempts'] as int? ?? 0,
      flashcardSessions: json['flashcard_sessions'] as int? ?? 0,
      totalStudyMinutes: json['total_study_minutes'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'level': level,
      'last_updated': lastUpdated,
      'status': status,
      'study_sessions': studySessions,
      'quiz_attempts': quizAttempts,
      'flashcard_sessions': flashcardSessions,
      'total_study_minutes': totalStudyMinutes,
    };
  }
}

class LearningInsight {
  final String type;
  final String value;
  final String description;

  LearningInsight({
    required this.type,
    required this.value,
    required this.description,
  });

  factory LearningInsight.fromJson(Map<String, dynamic> json) {
    // Handle case when json is null or missing fields
    if (json == null) {
      return LearningInsight(
        type: "unknown",
        value: "N/A",
        description: "No data available",
      );
    }

    return LearningInsight(
      type: json['type'] as String? ?? "unknown",
      value: json['value'] as String? ?? "N/A",
      description: json['description'] as String? ?? "",
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'value': value,
      'description': description,
    };
  }
}

class LearningPattern {
  final String userId;
  final Map<String, int> interactionCounts;
  final String studyRegularity;
  final List<LearningInsight> insights;

  LearningPattern({
    required this.userId,
    required this.interactionCounts,
    required this.studyRegularity,
    required this.insights,
  });

  factory LearningPattern.fromJson(Map<String, dynamic> json) {
    // Check if we have the new format with a learning_patterns field
    if (json.containsKey('learning_patterns')) {
      var learningPatterns = json['learning_patterns'];

      // Handle the new format where we get learning_patterns as a Map
      if (learningPatterns is Map) {
        return LearningPattern(
          userId: "default_user",
          interactionCounts: {},
          studyRegularity: learningPatterns['status']?.toString() ?? "none",
          insights: [
            LearningInsight(
                type: "message",
                value: "Info",
                description: learningPatterns['message']?.toString() ??
                    "No data available")
          ],
        );
      }
    }

    // Handle case when json is null or missing fields
    if (json == null) {
      return LearningPattern(
        userId: "unknown",
        interactionCounts: {},
        studyRegularity: "none",
        insights: [],
      );
    }

    return LearningPattern(
      userId: json['user_id'] as String? ?? "unknown",
      interactionCounts: json.containsKey('interaction_counts') &&
              json['interaction_counts'] != null
          ? (json['interaction_counts'] as Map<String, dynamic>)
              .map((k, v) => MapEntry(k, v as int))
          : {},
      studyRegularity: json['study_regularity'] as String? ?? "none",
      insights: json.containsKey('insights') && json['insights'] != null
          ? (json['insights'] as List)
              .map((e) => LearningInsight.fromJson(e as Map<String, dynamic>))
              .toList()
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'interaction_counts': interactionCounts,
      'study_regularity': studyRegularity,
      'insights': insights.map((e) => e.toJson()).toList(),
    };
  }
}

class LearningRecommendation {
  final String type;
  final String topic;
  final String reason;
  final String priority;

  LearningRecommendation({
    required this.type,
    required this.topic,
    required this.reason,
    required this.priority,
  });

  factory LearningRecommendation.fromJson(Map<String, dynamic> json) {
    return LearningRecommendation(
      type: json['type'] as String,
      topic: json['topic'] as String,
      reason: json['reason'] as String,
      priority: json['priority'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'topic': topic,
      'reason': reason,
      'priority': priority,
    };
  }
}

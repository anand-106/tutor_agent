import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'dart:convert';

class QuizWidget extends StatefulWidget {
  final Map<String, dynamic> quizData;

  QuizWidget({required this.quizData});

  @override
  _QuizWidgetState createState() => _QuizWidgetState();
}

class _QuizWidgetState extends State<QuizWidget> {
  int currentQuestionIndex = 0;
  Map<int, String> userAnswers = {};
  bool showResults = false;
  bool showExplanation = false;

  @override
  Widget build(BuildContext context) {
    final questions = widget.quizData['questions'] as List;
    final currentQuestion = questions[currentQuestionIndex];

    return SingleChildScrollView(
      child: Card(
        elevation: 4,
        margin: EdgeInsets.all(16),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Quiz header
              Text(
                widget.quizData['topic'],
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).primaryColor,
                ),
              ),
              SizedBox(height: 24),

              // Progress indicator
              LinearProgressIndicator(
                value: (currentQuestionIndex + 1) / questions.length,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(
                  Theme.of(context).primaryColor,
                ),
              ),
              Text(
                'Question ${currentQuestionIndex + 1}/${questions.length}',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.grey[600]),
              ),
              SizedBox(height: 24),

              // Question
              Text(
                currentQuestion['question'],
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
              ),
              SizedBox(height: 16),

              // Options
              ...List.generate(
                (currentQuestion['options'] as List).length,
                (index) => Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _getOptionColor(
                          currentQuestion['options'][index], currentQuestion),
                      foregroundColor: userAnswers[currentQuestionIndex] ==
                              currentQuestion['options'][index]
                          ? Colors.white
                          : Theme.of(context).primaryColor,
                      padding: EdgeInsets.all(16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: BorderSide(
                          color:
                              Theme.of(context).primaryColor.withOpacity(0.5),
                        ),
                      ),
                    ),
                    onPressed: () {
                      setState(() {
                        userAnswers[currentQuestionIndex] =
                            currentQuestion['options'][index];
                        showExplanation = true;
                      });
                    },
                    child: Text(
                      currentQuestion['options'][index],
                      style: TextStyle(fontSize: 16),
                    ),
                  ),
                ),
              ),

              // Explanation
              if (showExplanation && userAnswers[currentQuestionIndex] != null)
                Container(
                  margin: EdgeInsets.only(top: 16),
                  padding: EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Explanation:',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(currentQuestion['explanation']),
                    ],
                  ),
                ),

              SizedBox(height: 24),

              // Navigation buttons
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (currentQuestionIndex > 0)
                    ElevatedButton.icon(
                      icon: Icon(Icons.arrow_back),
                      label: Text('Previous'),
                      onPressed: () {
                        setState(() {
                          currentQuestionIndex--;
                          showExplanation =
                              userAnswers[currentQuestionIndex] != null;
                        });
                      },
                    ),
                  if (currentQuestionIndex < questions.length - 1)
                    ElevatedButton.icon(
                      icon: Icon(Icons.arrow_forward),
                      label: Text('Next'),
                      onPressed: userAnswers[currentQuestionIndex] != null
                          ? () {
                              setState(() {
                                currentQuestionIndex++;
                                showExplanation =
                                    userAnswers[currentQuestionIndex] != null;
                              });
                            }
                          : null,
                    )
                  else
                    ElevatedButton.icon(
                      icon: Icon(Icons.check),
                      label: Text('Finish Quiz'),
                      onPressed: userAnswers[currentQuestionIndex] != null
                          ? () => _showResults(context, questions)
                          : null,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getOptionColor(String option, Map<String, dynamic> question) {
    if (userAnswers[currentQuestionIndex] != option) {
      return Colors.white;
    }

    if (option == question['correct_answer']) {
      return Colors.green;
    }

    return Colors.red;
  }

  void _showResults(BuildContext context, List questions) {
    int correctAnswers = 0;
    for (int i = 0; i < questions.length; i++) {
      if (userAnswers[i] == questions[i]['correct_answer']) {
        correctAnswers++;
      }
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Quiz Results'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '$correctAnswers/${questions.length}',
              style: TextStyle(
                fontSize: 48,
                fontWeight: FontWeight.bold,
                color: Theme.of(context).primaryColor,
              ),
            ),
            Text(
              'Correct Answers',
              style: TextStyle(fontSize: 16, color: Colors.grey[600]),
            ),
            SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                setState(() {
                  currentQuestionIndex = 0;
                  userAnswers.clear();
                  showResults = false;
                });
              },
              child: Text('Retry Quiz'),
            ),
          ],
        ),
      ),
    );
  }
}

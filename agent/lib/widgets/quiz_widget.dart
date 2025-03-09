import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'dart:convert';
import 'package:google_fonts/google_fonts.dart';
import 'dart:ui';

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

  @override
  void initState() {
    super.initState();
    print('Initializing QuizWidget with data: ${widget.quizData}');

    // Validate quiz data structure
    final questions = widget.quizData['questions'] as List?;
    if (questions == null || questions.isEmpty) {
      print('Warning: Quiz initialized with no questions');
    } else {
      print('Quiz initialized with ${questions.length} questions');
      questions.asMap().forEach((index, question) {
        print('Question $index: $question');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final questions = widget.quizData['questions'] as List?;

    if (questions == null || questions.isEmpty) {
      print('Error: No questions available in quiz data');
      return Center(
        child: Text(
          'No questions available',
          style: GoogleFonts.inter(
            color: Colors.white.withOpacity(0.7),
            fontSize: 14,
          ),
        ),
      );
    }

    final currentQuestion =
        questions[currentQuestionIndex] as Map<String, dynamic>;

    return Container(
      constraints: BoxConstraints(maxWidth: 600), // Limit maximum width
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Colors.white.withOpacity(0.08),
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header with progress
                Container(
                  padding: EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: Colors.white.withOpacity(0.08),
                      ),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.quiz_outlined,
                            color: Theme.of(context).primaryColor,
                            size: 20,
                          ),
                          SizedBox(width: 8),
                          Text(
                            widget.quizData['topic'] ?? 'Quiz',
                            style: GoogleFonts.inter(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.white.withOpacity(0.9),
                            ),
                          ),
                          Spacer(),
                          Text(
                            '${currentQuestionIndex + 1}/${questions.length}',
                            style: GoogleFonts.inter(
                              fontSize: 14,
                              color: Colors.white.withOpacity(0.5),
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 12),
                      // Progress bar
                      Container(
                        height: 4,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(2),
                          color: Colors.white.withOpacity(0.1),
                        ),
                        child: FractionallySizedBox(
                          alignment: Alignment.centerLeft,
                          widthFactor:
                              (currentQuestionIndex + 1) / questions.length,
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(2),
                              color: Theme.of(context).primaryColor,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Question and options
                Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        currentQuestion['question'] ?? '',
                        style: GoogleFonts.inter(
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                          color: Colors.white.withOpacity(0.9),
                        ),
                      ),
                      SizedBox(height: 16),
                      // Options
                      ...List.generate(
                        (currentQuestion['options'] as List? ?? []).length,
                        (index) => Padding(
                          padding: EdgeInsets.only(bottom: 8),
                          child: _buildOptionButton(
                            (currentQuestion['options'] as List)[index]
                                .toString(),
                            currentQuestion,
                            context,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Explanation (if answered)
                if (userAnswers[currentQuestionIndex] != null)
                  Container(
                    padding: EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.03),
                      border: Border(
                        top: BorderSide(
                          color: Colors.white.withOpacity(0.08),
                        ),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              size: 16,
                              color: Theme.of(context).primaryColor,
                            ),
                            SizedBox(width: 8),
                            Text(
                              'Explanation',
                              style: GoogleFonts.inter(
                                fontWeight: FontWeight.w600,
                                color: Theme.of(context).primaryColor,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 8),
                        Text(
                          currentQuestion['explanation'] ?? '',
                          style: GoogleFonts.inter(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),

                // Navigation
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    border: Border(
                      top: BorderSide(
                        color: Colors.white.withOpacity(0.08),
                      ),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      if (currentQuestionIndex > 0)
                        _buildNavigationButton(
                          icon: Icons.arrow_back_rounded,
                          label: 'Previous',
                          onPressed: () {
                            setState(() {
                              currentQuestionIndex--;
                            });
                          },
                        )
                      else
                        SizedBox(width: 0),
                      if (currentQuestionIndex < questions.length - 1)
                        _buildNavigationButton(
                          icon: Icons.arrow_forward_rounded,
                          label: 'Next',
                          onPressed: userAnswers[currentQuestionIndex] != null
                              ? () {
                                  setState(() {
                                    currentQuestionIndex++;
                                  });
                                }
                              : null,
                        )
                      else
                        _buildNavigationButton(
                          icon: Icons.check_rounded,
                          label: 'Finish',
                          onPressed: userAnswers[currentQuestionIndex] != null
                              ? () => _showResults(context, questions)
                              : null,
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildOptionButton(
    String option,
    Map<String, dynamic> question,
    BuildContext context,
  ) {
    final bool isSelected = userAnswers[currentQuestionIndex] == option;
    final bool isCorrect = option == question['correct_answer'];
    final bool showResult = isSelected;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: userAnswers[currentQuestionIndex] == null
            ? () {
                setState(() {
                  userAnswers[currentQuestionIndex] = option;
                });
              }
            : null,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: showResult
                ? (isCorrect
                    ? Colors.green.withOpacity(0.1)
                    : Colors.red.withOpacity(0.1))
                : Colors.white.withOpacity(0.03),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: showResult
                  ? (isCorrect
                      ? Colors.green.withOpacity(0.3)
                      : Colors.red.withOpacity(0.3))
                  : isSelected
                      ? Theme.of(context).primaryColor.withOpacity(0.5)
                      : Colors.white.withOpacity(0.08),
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  option,
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    color: Colors.white.withOpacity(0.9),
                    fontWeight:
                        isSelected ? FontWeight.w500 : FontWeight.normal,
                  ),
                ),
              ),
              if (showResult)
                Icon(
                  isCorrect ? Icons.check_circle : Icons.cancel,
                  size: 16,
                  color: isCorrect ? Colors.green[400] : Colors.red[400],
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavigationButton({
    required IconData icon,
    required String label,
    required VoidCallback? onPressed,
  }) {
    return TextButton.icon(
      icon: Icon(icon, size: 18),
      label: Text(
        label,
        style: GoogleFonts.inter(
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
      style: TextButton.styleFrom(
        foregroundColor: Theme.of(context).primaryColor,
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      onPressed: onPressed,
    );
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
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
        child: Dialog(
          backgroundColor: Colors.transparent,
          child: Container(
            padding: EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Colors.white.withOpacity(0.08),
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Theme.of(context).primaryColor.withOpacity(0.1),
                  ),
                  child: Center(
                    child: Text(
                      '$correctAnswers/${questions.length}',
                      style: GoogleFonts.inter(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                  ),
                ),
                SizedBox(height: 16),
                Text(
                  'Quiz Complete!',
                  style: GoogleFonts.inter(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    color: Colors.white.withOpacity(0.9),
                  ),
                ),
                SizedBox(height: 24),
                ElevatedButton.icon(
                  icon: Icon(Icons.refresh_rounded, size: 18),
                  label: Text('Try Again'),
                  style: ElevatedButton.styleFrom(
                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {
                    Navigator.of(context).pop();
                    setState(() {
                      currentQuestionIndex = 0;
                      userAnswers.clear();
                      showResults = false;
                    });
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

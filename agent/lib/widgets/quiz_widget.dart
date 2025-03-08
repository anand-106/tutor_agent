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
  bool showExplanation = false;

  @override
  Widget build(BuildContext context) {
    final questions = widget.quizData['questions'] as List;
    final currentQuestion = questions[currentQuestionIndex];

    return SingleChildScrollView(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: Colors.white.withOpacity(0.08),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 10,
                  offset: Offset(0, 4),
                ),
              ],
            ),
            margin: EdgeInsets.all(16),
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Quiz header
                  Text(
                    widget.quizData['topic'],
                    style: GoogleFonts.inter(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).primaryColor,
                    ),
                  ),
                  SizedBox(height: 24),

                  // Progress indicator
                  Container(
                    height: 6,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(3),
                      color: Colors.white.withOpacity(0.1),
                    ),
                    child: FractionallySizedBox(
                      alignment: Alignment.centerLeft,
                      widthFactor:
                          (currentQuestionIndex + 1) / questions.length,
                      child: Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(3),
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                    ),
                  ),
                  SizedBox(height: 12),
                  Text(
                    'Question ${currentQuestionIndex + 1}/${questions.length}',
                    textAlign: TextAlign.center,
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      color: Colors.white.withOpacity(0.6),
                    ),
                  ),
                  SizedBox(height: 24),

                  // Question
                  Text(
                    currentQuestion['question'],
                    style: GoogleFonts.inter(
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                  SizedBox(height: 24),

                  // Options
                  ...List.generate(
                    (currentQuestion['options'] as List).length,
                    (index) => Padding(
                      padding: EdgeInsets.symmetric(vertical: 8),
                      child: _buildOptionButton(
                        currentQuestion['options'][index],
                        currentQuestion,
                        context,
                      ),
                    ),
                  ),

                  // Explanation
                  if (showExplanation &&
                      userAnswers[currentQuestionIndex] != null)
                    Container(
                      margin: EdgeInsets.only(top: 24),
                      padding: EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: Colors.white.withOpacity(0.08),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Explanation:',
                            style: GoogleFonts.inter(
                              fontWeight: FontWeight.bold,
                              color: Theme.of(context).primaryColor,
                              fontSize: 16,
                            ),
                          ),
                          SizedBox(height: 12),
                          Text(
                            currentQuestion['explanation'],
                            style: GoogleFonts.inter(
                              color: Colors.white.withOpacity(0.9),
                              fontSize: 15,
                            ),
                          ),
                        ],
                      ),
                    ),

                  SizedBox(height: 24),

                  // Navigation buttons
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      if (currentQuestionIndex > 0)
                        _buildNavigationButton(
                          icon: Icons.arrow_back_rounded,
                          label: 'Previous',
                          onPressed: () {
                            setState(() {
                              currentQuestionIndex--;
                              showExplanation =
                                  userAnswers[currentQuestionIndex] != null;
                            });
                          },
                        ),
                      if (currentQuestionIndex < questions.length - 1)
                        _buildNavigationButton(
                          icon: Icons.arrow_forward_rounded,
                          label: 'Next',
                          onPressed: userAnswers[currentQuestionIndex] != null
                              ? () {
                                  setState(() {
                                    currentQuestionIndex++;
                                    showExplanation =
                                        userAnswers[currentQuestionIndex] !=
                                            null;
                                  });
                                }
                              : null,
                        )
                      else
                        _buildNavigationButton(
                          icon: Icons.check_rounded,
                          label: 'Finish Quiz',
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

    Color getBackgroundColor() {
      if (!showResult) {
        return Colors.transparent;
      }
      return isCorrect
          ? Colors.green.withOpacity(0.2)
          : Colors.red.withOpacity(0.2);
    }

    Color getBorderColor() {
      if (!showResult) {
        return isSelected
            ? Theme.of(context).primaryColor
            : Colors.white.withOpacity(0.08);
      }
      return isCorrect
          ? Colors.green.withOpacity(0.5)
          : Colors.red.withOpacity(0.5);
    }

    return Container(
      decoration: BoxDecoration(
        color: getBackgroundColor(),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: getBorderColor()),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            setState(() {
              userAnswers[currentQuestionIndex] = option;
              showExplanation = true;
            });
          },
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    option,
                    style: GoogleFonts.inter(
                      fontSize: 16,
                      color: Colors.white.withOpacity(0.9),
                      fontWeight:
                          isSelected ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                ),
                if (showResult)
                  Icon(
                    isCorrect ? Icons.check_circle : Icons.cancel,
                    color: isCorrect ? Colors.green[400] : Colors.red[400],
                  ),
              ],
            ),
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
    return ElevatedButton.icon(
      icon: Icon(icon, size: 20),
      label: Text(
        label,
        style: GoogleFonts.inter(
          fontWeight: FontWeight.w600,
        ),
      ),
      style: ElevatedButton.styleFrom(
        backgroundColor: Theme.of(context).primaryColor.withOpacity(0.1),
        foregroundColor: Theme.of(context).primaryColor,
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        elevation: 0,
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
        child: AlertDialog(
          backgroundColor: Colors.white.withOpacity(0.1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          content: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$correctAnswers/${questions.length}',
                  style: GoogleFonts.inter(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).primaryColor,
                  ),
                ),
                Text(
                  'Correct Answers',
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    color: Colors.white.withOpacity(0.6),
                  ),
                ),
                SizedBox(height: 24),
                _buildNavigationButton(
                  icon: Icons.refresh_rounded,
                  label: 'Retry Quiz',
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

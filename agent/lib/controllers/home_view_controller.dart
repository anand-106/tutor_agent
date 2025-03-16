import 'package:get/get.dart';

class HomeViewController extends GetxController {
  final RxBool isLeftPanelExpanded = true.obs;

  void toggleSidePanel() {
    isLeftPanelExpanded.toggle();
  }

  void closeSidePanel() {
    isLeftPanelExpanded.value = false;
  }

  void openSidePanel() {
    isLeftPanelExpanded.value = true;
  }
}

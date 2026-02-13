import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "@/components/ThemeProvider";
import Login from "./pages/Login";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import Dashboard from "./pages/Dashboard";
import UsersPage from "./pages/admin/UsersPage";
import AttendancePage from "./pages/admin/AttendancePage";
import FinancePage from "./pages/admin/FinancePage";
import AcademicsPage from "./pages/admin/AcademicsPage";
import ExamsPage from "./pages/admin/ExamsPage";
import AnalyticsPage from "./pages/admin/AnalyticsPage";
import SchedulingPage from "./pages/admin/SchedulingPage";
import LibraryPage from "./pages/admin/LibraryPage";
import TransportPage from "./pages/admin/TransportPage";
import HostelPage from "./pages/admin/HostelPage";
import HRPayrollPage from "./pages/admin/HRPayrollPage";
import GovernancePage from "./pages/admin/GovernancePage";
import ActivityPointsPage from "./pages/admin/ActivityPointsPage";
import MeetingsPage from "./pages/admin/MeetingsPage";
import FeedbackPage from "./pages/admin/FeedbackPage";
import CalendarPage from "./pages/admin/CalendarPage";
import AnnouncementsPage from "./pages/admin/AnnouncementsPage";
import BillingPage from "./pages/admin/BillingPage";
import TeacherClassesPage from "./pages/teacher/TeacherClassesPage";
import TeacherGradingPage from "./pages/teacher/TeacherGradingPage";
import LessonPlansPage from "./pages/teacher/LessonPlansPage";
import QuestionBankPage from "./pages/teacher/QuestionBankPage";
import AttendanceMarkingPage from "./pages/teacher/AttendanceMarkingPage";
import StudentAnalyticsPage from "./pages/teacher/StudentAnalyticsPage";
import SyllabusPage from "./pages/teacher/SyllabusPage";
import StudentDashboardPage from "./pages/student/StudentDashboardPage";
import StudyTrainerPage from "./pages/student/StudyTrainerPage";
import AssignmentsPage from "./pages/student/AssignmentsPage";
import TimetablePage from "./pages/student/TimetablePage";
import FeesPage from "./pages/student/FeesPage";
import ExtracurricularPage from "./pages/student/ExtracurricularPage";
import VirtualClassroomPage from "./pages/student/VirtualClassroomPage";
import StudentAttendancePage from "./pages/student/StudentAttendancePage";
import ExamRegistrationPage from "./pages/student/ExamRegistrationPage";
import HallTicketPage from "./pages/student/HallTicketPage";
import ReportCardsPage from "./pages/shared/ReportCardsPage";
import ProfilePage from "./pages/shared/ProfilePage";
import ParentDashboardPage from "./pages/parent/ParentDashboardPage";
import ParentFeePaymentPage from "./pages/parent/ParentFeePaymentPage";
import ParentLeaveRequestPage from "./pages/parent/ParentLeaveRequestPage";
import ParentTransportTrackingPage from "./pages/parent/ParentTransportTrackingPage";
import ParentHostelInfoPage from "./pages/parent/ParentHostelInfoPage";
import ParentChildAttendancePage from "./pages/parent/ParentChildAttendancePage";
import AIScheduleMaker from "./components/ai/AIScheduleMaker";
import MessagesPage from "./pages/shared/MessagesPage";
import HelpdeskPage from "./pages/shared/HelpdeskPage";
import AIAssistantPage from "./pages/shared/AIAssistantPage";
import NotificationsPage from "./pages/shared/NotificationsPage";
import SettingsPage from "./pages/shared/SettingsPage";
import PricingPage from "./pages/PricingPage";
import DashboardLayout from "./components/DashboardLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import PlaceholderPage from "./pages/PlaceholderPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <ThemeProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/" element={<Navigate to="/login" replace />} />

            <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
              <Route path="/dashboard" element={<Dashboard />} />
              {/* Admin routes */}
              <Route path="/admin/users" element={<UsersPage />} />
              <Route path="/admin/academics" element={<AcademicsPage />} />
              <Route path="/admin/scheduling" element={<SchedulingPage />} />
              <Route path="/admin/attendance" element={<AttendancePage />} />
              <Route path="/admin/finance" element={<FinancePage />} />
              <Route path="/admin/exams" element={<ExamsPage />} />
              <Route path="/admin/analytics" element={<AnalyticsPage />} />
              <Route path="/admin/library" element={<LibraryPage />} />
              <Route path="/admin/transport" element={<TransportPage />} />
              <Route path="/admin/hostel" element={<HostelPage />} />
              <Route path="/admin/hr-payroll" element={<HRPayrollPage />} />
              <Route path="/admin/governance" element={<GovernancePage />} />
              <Route path="/admin/activity-points" element={<ActivityPointsPage />} />
              <Route path="/admin/meetings" element={<MeetingsPage />} />
              <Route path="/admin/feedback" element={<FeedbackPage />} />
              <Route path="/admin/calendar" element={<CalendarPage />} />
              <Route path="/admin/announcements" element={<AnnouncementsPage />} />
              <Route path="/admin/billing" element={<BillingPage />} />
              {/* Teacher routes */}
              <Route path="/teacher/classes" element={<TeacherClassesPage />} />
              <Route path="/teacher/grading" element={<TeacherGradingPage />} />
              <Route path="/teacher/lesson-plans" element={<LessonPlansPage />} />
              <Route path="/teacher/question-bank" element={<QuestionBankPage />} />
              <Route path="/teacher/attendance" element={<AttendanceMarkingPage />} />
              <Route path="/teacher/analytics" element={<StudentAnalyticsPage />} />
              <Route path="/teacher/syllabus" element={<SyllabusPage />} />
              {/* Student routes */}
              <Route path="/student/dashboard" element={<StudentDashboardPage />} />
              <Route path="/student/courses" element={<StudentDashboardPage />} />
              <Route path="/student/assignments" element={<AssignmentsPage />} />
              <Route path="/student/results" element={<ReportCardsPage />} />
              <Route path="/student/timetable" element={<TimetablePage />} />
              <Route path="/student/fees" element={<FeesPage />} />
              <Route path="/student/extracurricular" element={<ExtracurricularPage />} />
              <Route path="/student/virtual-classroom" element={<VirtualClassroomPage />} />
              <Route path="/student/attendance" element={<StudentAttendancePage />} />
              <Route path="/student/exam-registration" element={<ExamRegistrationPage />} />
              <Route path="/student/hall-ticket" element={<HallTicketPage />} />
              <Route path="/student/study-trainer" element={<StudyTrainerPage />} />
              {/* Parent routes */}
              <Route path="/parent/progress" element={<ParentDashboardPage />} />
              <Route path="/parent/fees" element={<ParentFeePaymentPage />} />
              <Route path="/parent/leave" element={<ParentLeaveRequestPage />} />
              <Route path="/parent/transport" element={<ParentTransportTrackingPage />} />
              <Route path="/parent/hostel" element={<ParentHostelInfoPage />} />
              <Route path="/parent/attendance" element={<ParentChildAttendancePage />} />
              {/* Shared routes */}
              <Route path="/messages" element={<MessagesPage />} />
              <Route path="/helpdesk" element={<HelpdeskPage />} />
              <Route path="/ai" element={<AIAssistantPage />} />
              <Route path="/notifications" element={<NotificationsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/ai-schedule" element={<AIScheduleMaker />} />
              <Route path="/pricing" element={<PricingPage />} />
            </Route>

            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;

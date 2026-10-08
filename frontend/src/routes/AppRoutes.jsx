import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/common/ProtectedRoute';

// Layouts
import TeacherLayout from '../layouts/TeacherLayout';
import StudentLayout from '../layouts/StudentLayout';

// Public Pages
import LandingPage from '../pages/public/LandingPage';
import LoginPage from '../pages/public/LoginPage';
import RegisterPage from '../pages/public/RegisterPage';

// Teacher Pages
import TeacherDashboard from '../pages/teacher/TeacherDashboard';
import TeacherClassrooms from '../pages/teacher/TeacherClassrooms';
import CreateClassroom from '../pages/teacher/CreateClassroom';
import ClassroomDetails from '../pages/teacher/ClassroomDetails';
import CreateProblem from '../pages/teacher/CreateProblem';
import ProblemDetails from '../pages/teacher/ProblemDetails';
import AIGenerateQuestionsPage from '../pages/teacher/AIGenerateQuestionsPage';
import TeacherAssignmentsPage from '../pages/teacher/TeacherAssignmentsPage';
import TeacherAssignmentDetailPage from '../pages/teacher/TeacherAssignmentDetailPage';
import TeacherStudentProfilePage from '../pages/teacher/TeacherStudentProfilePage';

// Student Pages
import StudentDashboard from '../pages/student/StudentDashboard';
import StudentClassrooms from '../pages/student/StudentClassrooms';
import JoinClassroom from '../pages/student/JoinClassroom';
import StudentClassroomDetails from '../pages/student/StudentClassroomDetails';
import ProblemList from '../pages/student/ProblemList';
import CodingWorkspace from '../pages/student/CodingWorkspace';
import SubmissionHistoryPage from '../pages/student/SubmissionHistory';
import StudentPerformancePage from '../pages/student/StudentPerformancePage';
import StudentAssignmentsPage from '../pages/student/StudentAssignmentsPage';
import StudentAssignmentDetailPage from '../pages/student/StudentAssignmentDetailPage';
import LearningPaths from '../pages/student/LearningPaths';

export const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Teacher Protected Routes */}
      <Route
        path="/teacher"
        element={
          <ProtectedRoute allowedRole="TEACHER">
            <TeacherLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<TeacherDashboard />} />
        <Route path="classrooms" element={<TeacherClassrooms />} />
        <Route path="classrooms/create" element={<CreateClassroom />} />
        <Route path="classrooms/:id" element={<ClassroomDetails />} />
        <Route path="classrooms/:id/students/:studentId" element={<TeacherStudentProfilePage />} />
        <Route path="assignments" element={<TeacherAssignmentsPage />} />
        <Route path="assignments/:id" element={<TeacherAssignmentDetailPage />} />
        <Route path="problems/create" element={<CreateProblem />} />
        <Route path="problems/ai-generate" element={<AIGenerateQuestionsPage />} />
        <Route path="problems/:id" element={<ProblemDetails />} />
      </Route>

      {/* Student Protected Routes */}
      <Route
        path="/student"
        element={
          <ProtectedRoute allowedRole="STUDENT">
            <StudentLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<StudentDashboard />} />
        <Route path="classrooms" element={<StudentClassrooms />} />
        <Route path="join" element={<JoinClassroom />} />
        <Route path="classrooms/:id" element={<StudentClassroomDetails />} />
        <Route path="assignments" element={<StudentAssignmentsPage />} />
        <Route path="assignments/:id" element={<StudentAssignmentDetailPage />} />
        <Route path="problems" element={<ProblemList />} />
        <Route path="problems/:id/code" element={<CodingWorkspace />} />
        <Route path="submissions" element={<SubmissionHistoryPage />} />
        <Route path="performance" element={<StudentPerformancePage />} />
        <Route path="learn" element={<LearningPaths />} />
      </Route>

      {/* Catch-all Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRoutes;

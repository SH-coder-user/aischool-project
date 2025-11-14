import type { ReactNode, CSSProperties } from "react";

interface MinwonLayoutProps {
  title: string;
  content: string;
  children?: ReactNode;
}

/* 바깥 전체 Wrapper */
const wrapperStyle: CSSProperties = {
  position: "relative",
  width: "100vw", // ← 브라우저 전체 너비
  height: "100vh",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  background: "#FBDA05",
  overflow: "hidden",
};

/* 하단 큰 흰색 카드 */
const whiteCardStyle: CSSProperties = {
  position: "absolute",
  bottom: "0",
  width: "100vw",
  height: "650px",
  background: "#FFFFFF",
  borderRadius: "150px 150px 0px 0px",
};

/* 상단 작은 흰 영역 */
const topWhiteStyle: CSSProperties = {
  position: "absolute",
  width: "375px",
  height: "129px",
  background: "#FFFFFF",
  top: "0",

  borderRadius: "0px 0px 60px 60px",
};

/* 상단 제목 */
const titleStyle: CSSProperties = {
  position: "absolute",
  top: "10px",
  width: "100%",
  textAlign: "center",
  fontFamily: "KoddiUD OnGothic",
  fontWeight: 800,
  fontSize: "75px",
  color: "#000000",
};

/* 본문 내용 */
const contentStyle: CSSProperties = {
  position: "relative",
  top: "-100px",
  width: "100%",
  textAlign: "center",
  fontFamily: "KoddiUD OnGothic",
  fontWeight: 700,
  fontSize: "110px",
  color: "#000000",
  padding: "0 40px",
};

export default function Layout({
  title,
  content,
  children,
}: MinwonLayoutProps) {
  return (
    <div style={wrapperStyle}>
      <div style={whiteCardStyle}></div>
      <div style={topWhiteStyle}></div>

      <div style={titleStyle}>{title}</div>
      <div style={contentStyle}>{content}</div>

      {children}
    </div>
  );
}

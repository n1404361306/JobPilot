import {
  AlignmentType,
  BorderStyle,
  Document,
  ImageRun,
  Packer,
  Paragraph,
  ShadingType,
  TextRun
} from "docx";
import { saveAs } from "file-saver";
import html2pdf from "html2pdf.js";
import type { ResumeFormSnapshot } from "@/composables/useResumeForm";
import { dataUrlToImagePayload } from "@/utils/photoUpload";
import { contactItems, hasProjects, hasText, skillGroups, textLines } from "@/utils/resumeHelpers";
import { getTemplatePreset, type ResumeTemplateId } from "@/utils/resumeTemplates";

function hexToDocxColor(hex: string) {
  return hex.replace("#", "").toUpperCase();
}

function sectionTitle(text: string, accent: string) {
  return new Paragraph({
    spacing: { before: 220, after: 120 },
    border: {
      bottom: {
        color: hexToDocxColor(accent),
        space: 4,
        style: BorderStyle.SINGLE,
        size: 8
      }
    },
    children: [
      new TextRun({
        text,
        bold: true,
        size: 24,
        color: hexToDocxColor(accent)
      })
    ]
  });
}

function bodyParagraph(text: string) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({ text, size: 21 })]
  });
}

function bulletParagraph(text: string) {
  return new Paragraph({
    spacing: { after: 60 },
    indent: { left: 360 },
    children: [new TextRun({ text: `• ${text}`, size: 21 })]
  });
}

function entryTitle(title: string, meta: string) {
  return new Paragraph({
    spacing: { before: 120, after: 60 },
    children: [
      new TextRun({ text: title, bold: true, size: 22 }),
      new TextRun({ text: meta ? `    ${meta}` : "", size: 20, color: "666666" })
    ]
  });
}

function photoParagraph(snapshot: ResumeFormSnapshot) {
  const payload = dataUrlToImagePayload(snapshot.basic_info.photo);
  if (!payload) {
    return null;
  }
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [
      new ImageRun({
        type: payload.type,
        data: payload.data,
        transformation: { width: 96, height: 120 }
      })
    ]
  });
}

function buildDocxChildren(snapshot: ResumeFormSnapshot, templateId: ResumeTemplateId) {
  const preset = getTemplatePreset(templateId);
  const accent = preset.accent;
  const name = snapshot.basic_info.name || "未命名简历";
  const children: Paragraph[] = [];

  const photo = photoParagraph(snapshot);
  if (photo) {
    children.push(photo);
  }

  if (templateId === "modern") {
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        shading: { type: ShadingType.CLEAR, fill: hexToDocxColor(accent), color: "auto" },
        spacing: { after: 120 },
        children: [new TextRun({ text: name, bold: true, size: 40, color: "FFFFFF" })]
      })
    );
  } else {
    children.push(
      new Paragraph({
        alignment: templateId === "classic" ? AlignmentType.CENTER : AlignmentType.LEFT,
        spacing: { after: 80 },
        children: [new TextRun({ text: name, bold: true, size: 44, color: hexToDocxColor(accent) })]
      })
    );
  }

  if (hasText(snapshot.job_intention)) {
    children.push(
      new Paragraph({
        alignment: templateId === "classic" || templateId === "modern" ? AlignmentType.CENTER : AlignmentType.LEFT,
        spacing: { after: 100 },
        children: [new TextRun({ text: snapshot.job_intention, size: 22, color: "444444" })]
      })
    );
  }

  const contacts = contactItems(snapshot)
    .map((item) => `${item.label}：${item.value}`)
    .join("  |  ");
  if (contacts) {
    children.push(
      new Paragraph({
        alignment: templateId === "classic" || templateId === "modern" ? AlignmentType.CENTER : AlignmentType.LEFT,
        spacing: { after: 160 },
        children: [new TextRun({ text: contacts, size: 20, color: "555555" })]
      })
    );
  }

  if (hasText(snapshot.summary)) {
    children.push(sectionTitle("个人简介", accent), bodyParagraph(snapshot.summary));
  }

  const skills = skillGroups(snapshot);
  if (skills.length) {
    children.push(sectionTitle("专业技能", accent));
    skills.forEach((item) => {
      children.push(bodyParagraph(`${item.label}：${item.value.replace(/\n/g, "、")}`));
    });
  }

  if (snapshot.education.length) {
    children.push(sectionTitle("教育经历", accent));
    snapshot.education.forEach((item) => {
      if (!hasText(item.school) && !hasText(item.major)) return;
      children.push(
        entryTitle(`${item.school} · ${item.major}`, `${item.degree}  ${item.period}`),
        bodyParagraph(`研究方向：${item.research_direction || "—"}    GPA：${item.gpa || "—"}`)
      );
      textLines(item.highlightsText).forEach((line) => children.push(bulletParagraph(line)));
    });
  }

  if (snapshot.internships.length) {
    children.push(sectionTitle("实习经历", accent));
    snapshot.internships.forEach((item) => {
      if (!hasText(item.company) && !hasText(item.position)) return;
      children.push(
        entryTitle(`${item.company} · ${item.position}`, `${item.period}  ${item.location}`),
        bodyParagraph(item.description)
      );
      textLines(item.responsibilitiesText).forEach((line) => children.push(bulletParagraph(line)));
      if (hasText(item.techStackText)) {
        children.push(bodyParagraph(`技术栈：${item.techStackText.replace(/\n/g, "、")}`));
      }
    });
  }

  if (hasProjects(snapshot)) {
    children.push(sectionTitle("项目经历", accent));
    snapshot.projects.forEach((item) => {
      if (!hasText(item.project_name) && !hasText(item.description)) return;
      children.push(
        entryTitle(`${item.project_name}`, `${item.type}  ${item.period}`),
        bodyParagraph(item.description)
      );
      textLines(item.responsibilitiesText).forEach((line) => children.push(bulletParagraph(line)));
      if (hasText(item.techStackText)) {
        children.push(bodyParagraph(`技术栈：${item.techStackText.replace(/\n/g, "、")}`));
      }
      textLines(item.resultsText).forEach((line) => children.push(bulletParagraph(line)));
    });
  }

  const extras = [
    { title: "科研经历", value: snapshot.researchText },
    { title: "获奖经历", value: snapshot.awardsText },
    { title: "证书", value: snapshot.certificatesText },
    { title: "开源贡献", value: snapshot.open_source },
    { title: "兴趣方向", value: snapshot.interests },
    { title: "个人评价", value: snapshot.self_evaluation }
  ].filter((item) => hasText(item.value));

  if (extras.length) {
    children.push(sectionTitle("其他", accent));
    extras.forEach((item) => children.push(bodyParagraph(`${item.title}：${item.value.replace(/\n/g, "；")}`)));
  }

  return children;
}

export async function exportResumePdf(element: HTMLElement, filename: string) {
  await html2pdf()
    .set({
      margin: [8, 8, 8, 8],
      filename: filename.endsWith(".pdf") ? filename : `${filename}.pdf`,
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, logging: false },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" }
    })
    .from(element)
    .save();
}

export async function exportResumeDocx(snapshot: ResumeFormSnapshot, templateId: ResumeTemplateId, filename: string) {
  const preset = getTemplatePreset(templateId);
  const doc = new Document({
    sections: [
      {
        properties: {
          page: {
            margin: { top: 720, right: 720, bottom: 720, left: 720 }
          }
        },
        children: buildDocxChildren(snapshot, templateId)
      }
    ],
    title: snapshot.basic_info.name || preset.name
  });

  const blob = await Packer.toBlob(doc);
  saveAs(blob, filename.endsWith(".docx") ? filename : `${filename}.docx`);
}

export function buildExportFilename(snapshot: ResumeFormSnapshot, fallback = "resume") {
  const name = snapshot.basic_info.name?.trim();
  return name ? `${name}-简历` : fallback;
}

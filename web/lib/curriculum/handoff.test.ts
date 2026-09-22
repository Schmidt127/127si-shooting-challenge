import { describe, expect, it } from "vitest";

import {
  curriculumGradeBandFromGrade,
  curriculumSourceGradeFromGrade,
  mintCurriculumHandoff,
} from "@/lib/curriculum/handoff";

describe("curriculumSourceGradeFromGrade", () => {
  it("normalizes kindergarten variants", () => {
    expect(curriculumSourceGradeFromGrade("K")).toBe("K");
    expect(curriculumSourceGradeFromGrade("k")).toBe("K");
    expect(curriculumSourceGradeFromGrade("Kindergarten")).toBe("K");
  });

  it("extracts numeric grades 1-12 from common enrollment strings", () => {
    expect(curriculumSourceGradeFromGrade("3")).toBe("3");
    expect(curriculumSourceGradeFromGrade("Grade 5")).toBe("5");
    expect(curriculumSourceGradeFromGrade("10th grade")).toBe("10");
    expect(curriculumSourceGradeFromGrade("12")).toBe("12");
  });

  it("returns null for missing or unrecognized grades (fail closed)", () => {
    expect(curriculumSourceGradeFromGrade("")).toBeNull();
    expect(curriculumSourceGradeFromGrade("   ")).toBeNull();
    expect(curriculumSourceGradeFromGrade("Pre-K")).toBeNull();
    expect(curriculumSourceGradeFromGrade("College")).toBeNull();
    expect(curriculumSourceGradeFromGrade("99")).toBeNull();
  });
});

describe("curriculumGradeBandFromGrade", () => {
  it("routes all five structured program bands deterministically", () => {
    expect(curriculumGradeBandFromGrade("K")).toBe("1-2");
    expect(curriculumGradeBandFromGrade("1")).toBe("1-2");
    expect(curriculumGradeBandFromGrade("2")).toBe("1-2");
    expect(curriculumGradeBandFromGrade("3")).toBe("3-4");
    expect(curriculumGradeBandFromGrade("4")).toBe("3-4");
    expect(curriculumGradeBandFromGrade("5")).toBe("5-6");
    expect(curriculumGradeBandFromGrade("6")).toBe("5-6");
    expect(curriculumGradeBandFromGrade("7")).toBe("7-8");
    expect(curriculumGradeBandFromGrade("8")).toBe("7-8");
    expect(curriculumGradeBandFromGrade("9")).toBe("9-12");
    expect(curriculumGradeBandFromGrade("10")).toBe("9-12");
    expect(curriculumGradeBandFromGrade("11")).toBe("9-12");
    expect(curriculumGradeBandFromGrade("12")).toBe("9-12");
  });

  it("returns null when grade cannot be mapped (fail closed)", () => {
    expect(curriculumGradeBandFromGrade("")).toBeNull();
    expect(curriculumGradeBandFromGrade("Pre-K")).toBeNull();
    expect(curriculumGradeBandFromGrade("College")).toBeNull();
    expect(curriculumGradeBandFromGrade("99")).toBeNull();
  });
});

describe("mintCurriculumHandoff", () => {
  it("mints a handoff for each structured band", async () => {
    const bands = [
      { grade: "1", expected: "1-2" },
      { grade: "4", expected: "3-4" },
      { grade: "6", expected: "5-6" },
      { grade: "8", expected: "7-8" },
      { grade: "11", expected: "9-12" },
    ] as const;

    for (const { grade } of bands) {
      const token = await mintCurriculumHandoff({
        enrollmentId: "recTestEnrollment01",
        grade,
        displayName: "Test Athlete",
      });
      expect(token).toMatch(/^[A-Za-z0-9_-]{40,60}$/);
    }
  });

  it("rejects handoff mint when grade band is unavailable", async () => {
    await expect(
      mintCurriculumHandoff({
        enrollmentId: "recTestEnrollment01",
        grade: "",
        displayName: "Test Athlete",
      }),
    ).rejects.toThrow("Curriculum grade band unavailable");
  });
});

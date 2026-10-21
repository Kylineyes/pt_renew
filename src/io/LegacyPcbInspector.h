#pragma once

#include "domain/DocumentInfo.h"

namespace pt {

class LegacyPcbInspector {
public:
    static InspectionResult inspect(const QString& filePath);
};

}
